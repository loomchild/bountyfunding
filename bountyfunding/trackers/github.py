from bountyfunding.core.const import IssueStatus
from bountyfunding.core.config import config
from bountyfunding.core.data import create_issue
from bountyfunding.core.errors import GithubError
from bountyfunding.util.api import GithubApi


def import_issue(project_id, issue_ref):
    api = GithubApi(token=config[project_id].GITHUB_TOKEN)

    r = api.get('/repos/loomchild/sandbox/issues/%s' % issue_ref)
    
    if r.status_code == 404:
        return None
        
    if r.status_code != 200:
        raise GithubError('Error accessing github repo', r)

    github_issue = r.json()

    status = IssueStatus.READY
    title = github_issue['title']
    number = github_issue['number']
    link = '/issues/%s' % number
    owner_id = None

    issue = create_issue(project_id, issue_ref, status, title, link, owner_id)
    
    return issue

