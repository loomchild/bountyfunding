from errors import APIException
from config import config
from models import Project, Token


DEFAULT_PROJECT = Project('Default', 'Default project', False, project_id=1)
DEFAULT_TOKEN = 'default'

TEST_PROJECTS = [
	Project('Test 1', 'First test project', True, project_id=-1),
	Project('Test 2', 'Second test project', True, project_id=-2),
	Project('Test 3', 'Third test project', True, project_id=-3),
]
TEST_TOKENS = {  
	'test': TEST_PROJECTS[0],
	'test1': TEST_PROJECTS[0],
	'test2': TEST_PROJECTS[1],
	'test3': TEST_PROJECTS[2],
}


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

	project = retrieve_project(token)
	if project != None:
		return project
	else:
		raise APIException("Invalid token", 403)


def retrieve_project(token):
	return Project.query.join(Token).filter_by(token=token).scalar()
		
