import bountyfunding
from bountyfunding.core.const import *
from bountyfunding.core.data import clean_database

from test import to_dict, to_object

from nose.tools import *


USER = "bountyfunding"

class Email_Test:

    def setup(self):
        self.app = bountyfunding.app.test_client()
        clean_database()
    
    def test_email(self):
        eq_(len(self.get_emails()), 0)
    
        r = self.app.post('/issues', data=dict(ref=1, status='READY', 
            title='Title', link='/issue/1'))
        eq_(r.status_code, 200)

        r = self.app.post('/issue/1/sponsorships', 
            data=dict(user=USER, amount=10))
        eq_(r.status_code, 200)

        r = self.app.get("/issue/1")
        eq_(r.status_code, 200)

        r = self.app.put('/issue/1', data=dict(
            status=IssueStatus.to_string(IssueStatus.STARTED)))
        eq_(r.status_code, 200)

        emails = self.get_emails()
        eq_(len(emails), 1)
        email = emails[0]
        eq_(email.recipient, USER)
        ok_(email.issue_id)
        ok_(email.body)

        r = self.app.delete("/email/%s" % email.id)
        eq_(r.status_code, 200)

    def get_emails(self):
        r = self.app.get("/emails")
        eq_(r.status_code, 200)
        return to_object(r, "data")

