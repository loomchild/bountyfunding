from utils import api, dict_to_object
from nose.tools import *


def teardown_module():
	api.delete("/issue/1")
	api.delete("/user/loomchild")

def test_validate_new_issue_fails():
	user = 'loomchild'
	amount = 10

	r = api.post('/issue/1/sponsorships', user=user, amount=amount)
	r = api.get("/issue/1")
	eq_(r.status_code, 200)

	r = api.put('/issue/1/sponsorship/%s/status' % user, status='VALIDATED')
	eq_(r.status_code, 400)

	r = api.get('/issue/1/sponsorship/%s' % user)
	eq_(r.status_code, 200)
	sponsorship = dict_to_object(r.json())
	eq_(sponsorship.status, 'NEW') 
