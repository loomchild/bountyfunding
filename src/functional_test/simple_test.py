from utils import api, dict_to_object
from nose.tools import *


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
	issue = dict_to_object(r.json())
	eq_(issue.status, 'NEW')

	r = api.get("/issue/1/sponsorships")
	eq_(r.status_code, 200)
	sponsorships = r.json()
	eq_(len(sponsorships), 1)
	sponsorship = dict_to_object(sponsorships[user])
	eq_(sponsorship.amount, amount) 
	eq_(sponsorship.status, 'PLEDGED') 

def test_sponsor_existing_issue_updates_it():
	user = 'pralinka'
	amount = 20
	
	r = api.post('/issue/1/sponsorships', user=user, amount=amount)
	r = api.get("/issue/1/sponsorships")
	eq_(r.status_code, 200)

	sponsorships = r.json()
	eq_(len(sponsorships), 2)
	sponsorship = dict_to_object(sponsorships[user])
	eq_(sponsorship.amount, amount) 
	eq_(sponsorship.status, 'PLEDGED') 

def test_sponsor_issue_by_same_user_updates_sponsorship():
	user = 'loomchild'
	amount = 30

	r = api.post('/issue/1/sponsorships', user=user, amount=amount)
	r = api.get("/issue/1")
	eq_(r.status_code, 200)
	issue = dict_to_object(r.json())
	eq_(issue.status, 'NEW')

	r = api.get("/issue/1/sponsorships")
	eq_(r.status_code, 200)
	sponsorships = r.json()
	eq_(len(sponsorships), 2)
	sponsorship = dict_to_object(sponsorships[user])
	eq_(sponsorship.amount, amount) 
	eq_(sponsorship.status, 'PLEDGED') 

