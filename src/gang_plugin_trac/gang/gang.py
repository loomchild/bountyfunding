from pprint import pprint

from genshi.filters import Transformer
from genshi.builder import tag

from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.web.api import ITemplateStreamFilter
from trac.ticket.api import ITicketChangeListener

import requests, re, urlparse

API_URL='http://localhost:5000'
SPONSOR_PATTERN = re.compile("/ticket/([0-9]+)/sponsor")

def call_gang_api(method, path, **kwargs):
	url = API_URL + path
	return requests.request(method, url, params=kwargs)
	

class GangPlugin(Component):
	implements(ITemplateStreamFilter, IRequestHandler, ITicketChangeListener)

	# ITemplateStreamFilter methods
	def filter_stream(self, req, method, filename, stream, data):
		"""
		Quick and dirty solution - modify page on the fly to inject special field. It would be
		nicer if we can do it by creating custom field as this depends on page structure.
		"""
		if filename == 'ticket.html':
			ticket = data.get('ticket')
			if ticket and ticket.exists:
				identifier = ticket.id
				user = req.authname
				request = call_gang_api('GET', '/issue/%s' % identifier)
				fragment = tag()
				user_amount = 0
				total_amount = 0
				status = convert_status(ticket.values['status'])
				owner = ticket.values['status']
				if request.status_code == 200:
					json = request.json()
					total_amount = json.get('total_amount', 0)
					fragment.append(u"%d\u20ac" % total_amount)
					request = call_gang_api('GET', '/issue/%s/sponsorship' % identifier, user=user)
					if request.status_code == 200:
						user_amount = request.json().get('amount', 0)

				elif request.status_code == 404:
					fragment.append("Not sponsored yet")
				else:
					fragment.append("Error occured")

				if user != None and user != 'anonymous' and status == 'NEW':
					fragment.append(" ")
					#fragment.append(tag.div(id="slider"))
					#fragment.append(tag.script("(function($) { $('#slider').slider(); })(jQuery)"))
					fragment.append(tag.form(tag.input(name="amount", type="text", size="3", style="font-size: 100%; vertical-align: baseline;", value=user_amount), tag.input(name="user", type="hidden", value=user), tag.input(type="submit", value="Sponsor", style="font-size: 100%; vertical-align: baseline;"), action="/ticket/%s/sponsor" % identifier, style="display: inline;"))
					#fragment.append(tag.a("Sponsor", href="/ticket/%s/sponsor?amount=100" % identifier))

				elif status == 'ASSIGNED':
					if owner == user:
						fragment.append(u' (Unconfirmed: %d\u20ac)' % total_amount)
					else:
						pass

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
		call_gang_api('POST', '/issue/%s/sponsorships' % ticket_id, user=req.authname, amount=amount[0])
		req.redirect('/ticket/%s' % ticket_id)


	# ITicketChangeListener methods
	def ticket_created(self, ticket):
		pass

	def ticket_changed(self, ticket, comment, author, old_values):
		if 'status' in old_values:
			status = convert_status(ticket.values['status'])
			call_gang_api('POST', '/issue/%s/status' % ticket.id, status=status)

	def ticket_deleted(self, ticket):
		pass

def convert_status(status):
	table = {'new':'NEW', 'accepted':'ASSIGNED', 'assigned':'ASSIGNED', 'reopened':'NEW', 'closed':'COMPLETED'}
	return table[status]
