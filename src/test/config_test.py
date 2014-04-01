from nose.tools import *
from mock import MagicMock
from config import ProjectConfig
from bountyfunding_api.models import Config

def test_project_config():
	project_id = 5
	name = 'max_pledge_amount'
	value = 9
	pc = ProjectConfig(project_id)
	pc._get_property = MagicMock(return_value=Config(project_id, name, value))

	v = pc.MAX_PLEDGE_AMOUNT
	eq_(value, v)
	pc._get_property.assert_called_with(project_id, name)
	
