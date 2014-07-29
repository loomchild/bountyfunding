from errors import APIException
from config import config
from models import Project, Token
from const import ProjectType


DEFAULT_PROJECT = Project('Default', 'Default project', ProjectType.NORMAL, project_id=1)
DEFAULT_TOKEN = 'default'

TEST_PROJECTS = [
	Project('Test 1', 'First test project', ProjectType.TEST, project_id=-1),
	Project('Test 2', 'Second test project', ProjectType.TEST, project_id=-2),
	Project('Test 3', 'Third test project', ProjectType.TEST,project_id=-3),
]
TEST_TOKENS = {  
	'test': TEST_PROJECTS[0],
	'test1': TEST_PROJECTS[0],
	'test2': TEST_PROJECTS[1],
	'test3': TEST_PROJECTS[2],
}

ROOT_PROJECT = Project('Root', 'Root project', ProjectType.ROOT, project_id=0)
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
		
