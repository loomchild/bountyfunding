from pprint import pprint

from genshi.filters import Transformer
from genshi.builder import tag

from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.web.api import ITemplateStreamFilter

import requests, re, urlparse

API_URL='http://localhost:5000'
SPONSOR_PATTERN = re.compile("/ticket/([0-9]+)/sponsor")

def call_gang_api(method, path, **kwargs):
	url = API_URL + path
	return requests.request(method, url, params=kwargs)
	

class GangPlugin(Component):
	implements(ITemplateStreamFilter, IRequestHandler)

	# ITemplateStreamFilter methods
	def filter_stream(self, req, method, filename, stream, data):
		"""
		Quick and dirty solution - modify page on the fly to inject special field. It would be
		much nicer if we can do it by creating custom field as this depends on page structure.
		"""
		if filename == 'ticket.html':
			ticket = data.get('ticket')
			if ticket and ticket.exists:
				identifier = ticket.id
				user = req.authname
				request = call_gang_api('GET', '/issue/%s' % identifier)
				fragment = tag()
				if request.status_code == 200:
					amount = request.json().get('amount', 0)
					fragment.append(u"%d\u20ac" % amount)
				elif request.status_code == 404:
					fragment.append("Not sponsored yet")
				else:
					fragment.append("Error occured")

				if user != None and user != 'anonymous':
					fragment.append(" ")
					#fragment.append(tag.div(id="slider"))
					#fragment.append(tag.script("(function($) { $('#slider').slider(); })(jQuery)"))
					#fragment.append(tag.form(tag.input(name="amount", type="text", size="5"), tag.input(name=user, type="hidden", value=user), tag.input(type="submit")))
					fragment.append(tag.a("Sponsor", href="/ticket/%s/sponsor?amount=100" % identifier))

				#Alternatively add custom field to ticket object
				filter = Transformer('.//table[@class="properties"]	')
				stream |= filter.append(tag.tr(tag.th(" Gang: ", id="h_gang"), tag.td(fragment, headers="h_gang")))
		return stream

	# IRequestHandler methods
	def match_request(self, req):
		return SPONSOR_PATTERN.match(req.path_info) != None
	
	def process_request(self, req):
		ticket_id = SPONSOR_PATTERN.match(req.path_info).group(1)
		query = urlparse.parse_qs(req.query_string)
		amount = query['amount']
		call_gang_api('POST', '/issue/%s/sponsors' % ticket_id, user=req.authname, amount=amount[0])
		req.redirect('/ticket/%s' % ticket_id)

