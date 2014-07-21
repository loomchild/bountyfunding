from utils import Api, dict_to_object
from const import *
from nose.tools import *


TOKEN = 'test';
USER = "loomchild"


api = Api(TOKEN)


def teardown():
	r = api.delete('/')
	eq_(r.status_code, 200)


def test_email():
	eq_(len(get_emails()), 0)

	r = api.post('/issue/1/sponsorships', user=USER, amount=10)
	r = api.get("/issue/1")
	eq_(r.status_code, 200)

	r = api.put('/issue/1', status=IssueStatus.to_string(IssueStatus.STARTED))
	eq_(r.status_code, 200)

	emails = get_emails()
	eq_(len(emails), 1)
	email = emails[0]
	eq_(email.recipient, USER)
	ok_(email.issue_id)
	ok_(email.body)


def get_emails():
	r = api.get("/emails")
	eq_(r.status_code, 200)
	emails = [dict_to_object(email) for email in r.json().get('data')]
	return emails

