from bountyfunding.core.const import IssueStatus
from bountyfunding.core.config import config
from bountyfunding.core.data import retrieve_issue, create_issue, update_issue, retrieve_create_user
from bountyfunding.core.models import Project
from bountyfunding.util.api import GithubApi
import re


def create_update_issue(project_id, issue_ref):
    api = GithubApi(token=config[project_id].GITHUB_TOKEN)
    github_issue = api.get('/repos/%s/issues/%s' % (config[project_id].TRACKER_PROJECT, issue_ref))
    if github_issue == None:
        return None
    
    issue = create_update_issue_from_github_issue(project_id, github_issue)
    update_button(project_id, github_issue)
    return issue

RESULTS_PER_PAGE = 100

def sync_issues(project_id):
    project = Project.query.get(project_id)
    api = GithubApi(token=config[project_id].GITHUB_TOKEN)
    updated_issues = []
    page = 1

    while True:
        github_issues = api.get('/repos/%s/issues' % config[project_id].TRACKER_PROJECT,
                per_page=RESULTS_PER_PAGE, page=page)

        if not github_issues:
            break

        for github_issue in github_issues:
            issue = create_update_issue_from_github_issue(project_id, github_issue)
            button = update_button(project, github_issue)
            if issue or button:
                updated_issues.append(github_issue.number)
        
        page += 1

    return updated_issues

def create_update_issue_from_github_issue(project_id, github_issue):
    """Returns None when issue has not been update"""
    issue_ref = github_issue.number
    title = github_issue.title
    link = get_link(github_issue)
    status = get_status(github_issue)
    owner_id = get_owner_id(github_issue, project_id)

    issue = retrieve_issue(project_id, issue_ref)
    if issue == None:
        issue = create_issue(project_id, issue_ref, status, title, link, owner_id)
    elif (issue.status != status or issue.title != title or
            issue.link != link or issue.owner_id != owner_id):
        issue.status = status
        issue.title = title
        issue.link = link
        issue.owner_id = owner_id
        update_issue(issue)
    else:
        return None
    
    return issue

def get_link(github_issue):
    number = github_issue.number
    link = '/issues/%s' % number
    return link

def get_status(github_issue):
    state = github_issue.state
    assignee = github_issue.assignee
    status = IssueStatus.READY
    if state == "closed":
        status = IssueStatus.COMPLETED
    elif assignee != None:
        status = IssueStatus.STARTED
    return status

def get_owner_id(github_issue, project_id):
    owner_id = None
    assignee = github_issue.assignee
    if assignee:
        login = assignee.login
        user = retrieve_create_user(project_id, login)
        owner_id = user.user_id
    return owner_id 

def update_button(project, github_issue):
    issue_ref = github_issue.number
    body = github_issue.body
    body = remove_button(body)
    body = add_button(body, project, issue_ref)
    
    if body != github_issue.body:
        api = GithubApi(token=config[project.project_id].GITHUB_TOKEN)
        api.patch('/repos/%s/issues/%s' % (config[project.project_id].TRACKER_PROJECT, issue_ref), data=dict(body=body))
        return True

    return False
     
button_pattern = re.compile(r'^\[!\[Bounty\].*\n', flags=re.M)

def remove_button(body):
    return re.sub(button_pattern, "", body)

def add_button(body, project, issue_ref):
    base_url = config.URL
    image_url = "%s/projects/%s/issues/%s.svg" % (base_url, project.name, issue_ref)
    issue_url = "%s/projects/%s/issues/%s.html" % (base_url, project.name, issue_ref)
    button = "[![Bounty](%s)](%s)\n" % (image_url, issue_url)
    return button + body

