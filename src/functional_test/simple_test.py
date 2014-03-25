from utils import Api, dict_to_object
from const import SponsorshipStatus, PaymentStatus, PaymentGateway
from nose.tools import *


PROJECT_ID = -1;


api = Api(PROJECT_ID)


def teardown_module():
	r = api.delete('/')
	eq_(r.status_code, 200)


def test_version():
	r = api.get("/version")
	eq_(r.status_code, 200)

def test_retrieving_nonexisting_issue_returns_404():
	r = api.get("/issue/1")
	eq_(r.status_code, 404)

def test_sponsor_nonexisting_issue_creates_it():
	user = 'loomchild'
	amount = 10

	r = api.get("/issue/1")
	eq_(r.status_code, 404)
	r = api.post('/issue/1/sponsorships', user=user, amount=amount)
	r = api.get("/issue/1")
	eq_(r.status_code, 200)
	r = api.get("/issue/1/sponsorships")
	eq_(r.status_code, 200)
	sponsorships = r.json()
	eq_(len(sponsorships), 1)
	sponsorship = dict_to_object(sponsorships[user])
	eq_(sponsorship.amount, amount) 
	eq_(SponsorshipStatus.from_string(sponsorship.status), 
			SponsorshipStatus.PLEDGED) 

def test_sponsor_existing_issue_updates_it():
	user = 'pralinka'
	amount = 5
	
	r = api.post('/issue/1/sponsorships', user=user, amount=amount)
	eq_(r.status_code, 200)
	r = api.get("/issue/1/sponsorships")
	eq_(r.status_code, 200)
	sponsorships = r.json()
	eq_(len(sponsorships), 2)
	sponsorship = dict_to_object(sponsorships[user])
	eq_(sponsorship.amount, amount) 
	eq_(SponsorshipStatus.from_string(sponsorship.status), 
			SponsorshipStatus.PLEDGED) 

def test_update_amount():
	user = 'loomchild'
	amount = 8

	r = api.put('/issue/1/sponsorship/%s' % user, amount=amount)
	eq_(r.status_code, 200)
	r = api.get("/issue/1/sponsorships")
	eq_(r.status_code, 200)
	sponsorships = r.json()
	eq_(len(sponsorships), 2)
	sponsorship = dict_to_object(sponsorships[user])
	eq_(sponsorship.amount, amount) 
	eq_(SponsorshipStatus.from_string(sponsorship.status), 
			SponsorshipStatus.PLEDGED) 

