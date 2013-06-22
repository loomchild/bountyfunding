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
GANG_TICKET_PATTERN = re.compile("/ticket/([0-9]+)/(sponsor|confirm|validate)")

def call_gang_api(method, path, **kwargs):
	url = API_URL + path
	return requests.request(method, url, params=kwargs)

class Sponsorship:
	def __init__(self, dictionary={}):
		self.amount = dictionary.get('amount', 0)
		self.status = dictionary.get('status')

def convert_status(status):
	table = {'new':'NEW', 'accepted':'ASSIGNED', 'assigned':'ASSIGNED', 'reopened':'NEW', 'closed':'COMPLETED'}
	return table[status]

def sum_amounts(sponsorships, statuses=None):
	if statuses != None:
		sponsorships = [s for s in sponsorships if s.status in statuses]
	total_amount = sum(map(lambda s: s.amount, sponsorships))
	return total_amount


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
				user = req.authname if req.authname != 'anonymous' else None
				request = call_gang_api('GET', '/issue/%s' % identifier)
				fragment = tag()
				sponsorships = {}
				status = convert_status(ticket.values['status'])
				owner = ticket.values['owner']
				if request.status_code == 200:
					
					request = call_gang_api('GET', '/issue/%s/sponsorships' % identifier)
					if request.status_code == 200:
						sponsorships =  {k:Sponsorship(v) for k, v in request.json().items()}
					
					pledged_amount = sum_amounts(sponsorships.values())
					user_sponsorship = sponsorships.get(user, Sponsorship())

					# Bounty
					tooltip = u"Pledged: %d\u20ac" % pledged_amount
					
					if status == 'ASSIGNED' or status == 'COMPLETED':
						confirmed_amount = sum_amounts(sponsorships.values(), ('CONFIRMED', 'VALIDATED'))
						tooltip += u" \nConfirmed: %d\u20ac" % confirmed_amount
					if status == 'COMPLETED':
						validated_amount = sum_amounts(sponsorships.values(), 'VALIDATED')
						tooltip += u" \nValidated: %d\u20ac" % validated_amount
					
					fragment.append(tag.span(u"%d\u20ac" % pledged_amount, title=tooltip))

					# Action
					action = None
						
					if ((status == 'ASSIGNED' or status == 'COMPLETED') 
							and user_sponsorship.status == 'PLEDGED'):
						action = tag.form(tag.input(name="user", type="hidden", value=user), " ", tag.input(type="submit", value=u"Confirm %d\u20ac" % user_sponsorship.amount, style="font-size: 100%; vertical-align: baseline;"), action="/ticket/%s/confirm" % identifier, style="display: inline;")

					elif status == 'COMPLETED' and user_sponsorship.status == 'CONFIRMED':
						action = tag.form(tag.input(name="user", type="hidden", value=user), " ", tag.input(type="submit", value=u"Validate %d\u20ac" % user_sponsorship.amount, style="font-size: 100%; vertical-align: baseline;"), action="/ticket/%s/validate" % identifier, style="display: inline;")

					elif (status != 'COMPLETED' and (status == 'NEW' or user_sponsorship.amount == 0) 
							and user != None 
							and user_sponsorship.status == None or user_sponsorship.status == 'PLEDGED'):
						action = tag.form(tag.input(name="amount", type="text", size="3", style="font-size: 100%; vertical-align: baseline;", value=user_sponsorship.amount), tag.input(name="user", type="hidden", value=user), tag.input(type="submit", value="Pledge", style="font-size: 100%; vertical-align: baseline;"), action="/ticket/%s/sponsor" % identifier, style="display: inline;")
					
					if action != None:
						fragment.append(" ")
						fragment.append(action)
						
				elif request.status_code == 404:
					fragment.append("Not sponsored yet")
				else:
					fragment.append("Error occured")
	
				filter = Transformer('.//table[@class="properties"]	')
				gang_tag = tag.tr(tag.th("Bounty: ", id="h_gang"), tag.td(fragment, headers="h_gang")) 
				stream |= filter.append(gang_tag)
		return stream

	# IRequestHandler methods
	def match_request(self, req):
		return GANG_TICKET_PATTERN.match(req.path_info) != None
	
	def process_request(self, req):
		match = GANG_TICKET_PATTERN.match(req.path_info)
		ticket_id = match.group(1)
		action = match.group(2)
		query = urlparse.parse_qs(req.query_string)

		if action == 'sponsor':
			amount = query['amount']
			call_gang_api('POST', '/issue/%s/sponsorships' % ticket_id, user=req.authname, amount=amount[0])
		elif action == 'confirm':
			call_gang_api('PUT', '/issue/%s/sponsorships' % ticket_id, user=req.authname, status='CONFIRMED')
		elif action == 'validate':
			call_gang_api('PUT', '/issue/%s/sponsorships' % ticket_id, user=req.authname, status='VALIDATED')
		
		req.redirect('/ticket/%s' % ticket_id)


	# ITicketChangeListener methods
	def ticket_created(self, ticket):
		pass

	def ticket_changed(self, ticket, comment, author, old_values):
		if 'status' in old_values:
			status = convert_status(ticket.values['status'])
			call_gang_api('PUT', '/issue/%s/status' % ticket.id, status=status)

	def ticket_deleted(self, ticket):
		pass

