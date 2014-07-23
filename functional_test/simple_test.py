from utils import Api, dict_to_object
from const import IssueStatus, SponsorshipStatus, PaymentStatus, PaymentGateway
from nose.tools import *


TOKEN = 'test';


api = Api(TOKEN)


def teardown_module():
	r = api.delete('/')
	eq_(r.status_code, 200)


def test_version():
	r = api.get("/version")
	eq_(r.status_code, 200)

def test_retrieving_nonexisting_issue_returns_404():
	r = api.get("/issue/1")
	eq_(r.status_code, 404)

def test_sponsor_nonexisting_issue_returns_404():
	user = 'loomchild'
	amount = 10
	r = api.get("/issue/1")
	eq_(r.status_code, 404)
	r = api.post('/issue/1/sponsorships', user=user, amount=amount)
	eq_(r.status_code, 404)

def test_create_issue():
	status = IssueStatus.READY
	title = 'TestTitle'
	link = '/issue/1'

	r = api.get("/issue/1")
	eq_(r.status_code, 404)

	r = api.post('/issues', ref=1, status=IssueStatus.to_string(status), title=title, link=link)
	eq_(r.status_code, 200)
	
	r = api.get("/issue/1")
	eq_(r.status_code, 200)
	issue = dict_to_object(r.json())
	eq_(issue.ref, '1')
	eq_(IssueStatus.from_string(issue.status), status)
	eq_(issue.title, title)
	eq_(issue.link, 'http://localhost:8100' + link)

def test_sponsor_issue():
	user = 'loomchild'
	amount = 3

	r = api.post('/issue/1/sponsorships', user=user, amount=amount)
	eq_(r.status_code, 200)
	r = api.get("/issue/1/sponsorships")
	eq_(r.status_code, 200)
	sponsorships = r.json()
	eq_(len(sponsorships), 1)
	sponsorship = dict_to_object(sponsorships[user])
	eq_(sponsorship.amount, amount) 
	eq_(SponsorshipStatus.from_string(sponsorship.status), 
			SponsorshipStatus.PLEDGED) 

def test_sponsor_issue_2():
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

