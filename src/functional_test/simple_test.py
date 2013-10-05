from utils import api
from nose.tools import *


def test():
	r = api.post('/issue/1/sponsorships', user='loomchild', amount=10)
	r = api.get("/issue/1")
	eq_(r.status_code, 200)
