from utils import api
from nose.tools import *

def test_retrieving_nonexisting_issue_returns_404():
	r = api.get("/issue/1")
	eq_(r.status_code, 404)

