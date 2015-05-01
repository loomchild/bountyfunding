from bountyfunding.core.const import IssueStatus
from bountyfunding.core.config import config
from bountyfunding.core.data import create_issue
from bountyfunding.util.api import GithubApi

#TODO: move to errors, make more generic
class GithubError(Exception):
    
    def __init__(self, message="", result=None):
        self.message = message
        if result != None:
            self.message += "; code = %s, message = %s" % (result.status_code, result.json())

    def __str__(self):
        return self.message

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

