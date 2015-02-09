from bountyfunding.api.errors import APIException
from bountyfunding.api.config import config
from bountyfunding.api.models import Project, Token
from bountyfunding.api.const import ProjectType


class ImmutableProject:

    def __init__(self, project_id, name, description, type):
        self.project_id = project_id
        self.name = name
        self.description = description
        self.type = type

    def is_mutable(self):
        return False


DEFAULT_PROJECT = ImmutableProject(1, 'Default', 'Default project', ProjectType.NORMAL)
DEFAULT_TOKEN = 'default'

TEST_PROJECTS = [
    ImmutableProject(-1, 'Test 1', 'First test project', ProjectType.TEST),
    ImmutableProject(-2, 'Test 2', 'Second test project', ProjectType.TEST),
    ImmutableProject(-3, 'Test 3', 'Third test project', ProjectType.TEST),
]
TEST_TOKENS = {  
    'test': TEST_PROJECTS[0],
    'test1': TEST_PROJECTS[0],
    'test2': TEST_PROJECTS[1],
    'test3': TEST_PROJECTS[2],
}

ROOT_PROJECT = ImmutableProject(0, 'Root', 'Root project', ProjectType.ROOT)
ROOT_TOKEN = 'root'

def get_project(token):
    if not token or token == DEFAULT_TOKEN:
        if config.PROJECT_DEFAULT:
            return DEFAULT_PROJECT
        else:
            raise APIException("Default token disabled", 403)

        
    if token in TEST_TOKENS:
        if config.PROJECT_TEST:
            return TEST_TOKENS[token]
        else:
            raise APIException("Test tokens disabled", 403)

    if token == ROOT_TOKEN:
        if config.PROJECT_ROOT:
            return ROOT_PROJECT
        else:
            raise APIException("Root token disabled", 403)

    project = retrieve_project(token)
    if project != None:
        return project
    else:
        raise APIException("Invalid token", 403)


def retrieve_project(token):
    return Project.query.join(Token).filter_by(token=token).scalar()
        
