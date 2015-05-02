from bountyfunding.core.const import IssueStatus
from bountyfunding.core.config import config
from bountyfunding.core.data import create_issue, retrieve_create_user
from bountyfunding.core.errors import GithubError
from bountyfunding.util.api import GithubApi


def import_issue(project_id, issue_ref):
    api = GithubApi(token=config[project_id].GITHUB_TOKEN)

    github_issue = api.get('/repos/loomchild/sandbox/issues/%s' % issue_ref)
    
    if github_issue == None:
        return None
        
    title = github_issue.title
    link = get_link(github_issue)
    status = get_status(github_issue)
    owner_id = get_owner_id(github_issue, project_id)

    issue = create_issue(project_id, issue_ref, status, title, link, owner_id)
    
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

