from pprint import pprint

from genshi.filters import Transformer
from genshi.builder import tag

from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.web.api import ITemplateStreamFilter
from trac.ticket.api import ITicketChangeListener

from trac.notification import NotifyEmail

import requests, re
from pkg_resources import resource_filename


API_URL='http://localhost:5000'
GANG_PATTERN = re.compile("(?:/(?P<ticket>ticket)/(?P<ticket_id>[0-9]+)/(?P<ticket_action>sponsor|confirm|validate))|(?:/(?P<gang>gang)/(?P<gang_action>email))")

def call_gang_api(method, path, **kwargs):
	url = API_URL + path
	return requests.request(method, url, params=kwargs)

class Sponsorship:
	def __init__(self, dictionary={}):
		self.amount = dictionary.get('amount', 0)
		self.status = dictionary.get('status')

class Email:
	def __init__(self, dictionary):
		self.id = dictionary.get('id')
		self.recipient = dictionary.get('recipient')
		self.subject = dictionary.get('subject')
		self.body = dictionary.get('body')

def convert_status(status):
	table = {'new':'NEW', 'accepted':'ASSIGNED', 'assigned':'ASSIGNED', 'reopened':'NEW', 'closed':'COMPLETED'}
	return table[status]

def sum_amounts(sponsorships, statuses=None):
	if statuses != None:
		sponsorships = [s for s in sponsorships if s.status in statuses]
	total_amount = sum(map(lambda s: s.amount, sponsorships))
	return total_amount


class GangPlugin(Component):
	implements(ITemplateStreamFilter, IRequestHandler, ITemplateProvider, ITicketChangeListener)

	# ITemplateStreamFilter methods
	def filter_stream(self, req, method, filename, stream, data):
		"""
		Quick and dirty solution - modify page on the fly to inject special field. It would be
		nicer if we can do it by creating custom field as this depends on page structure.
		"""
		if filename == 'ticket.html' or filename == 'bh_ticket.html':
			bloodhound = (filename == 'bh_ticket.html')
			ticket = data.get('ticket')
			if ticket and ticket.exists:
				identifier = ticket.id
				user = req.authname if req.authname != 'anonymous' else None
				request = call_gang_api('GET', '/issue/%s' % identifier)
				fragment = tag()
				sponsorships = {}
				status = convert_status(ticket.values['status'])
				owner = ticket.values['owner']
				if request.status_code == 200 or request.status_code == 404:
					
					sponsorships = {}
					request = call_gang_api('GET', '/issue/%s/sponsorships' % identifier)
					if request.status_code == 200:
						sponsorships = dict(map(lambda (k,v): (k, Sponsorship(v)), request.json().items()))
					
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
						action = tag.form(tag.input(type="submit", value=u"Confirm %d\u20ac" % user_sponsorship.amount), method="post", action="/ticket/%s/confirm" % identifier)

					elif status == 'COMPLETED' and user_sponsorship.status == 'CONFIRMED':
						action = tag.form(tag.input(type="submit", name='accept', value=u"Validate %d\u20ac" % user_sponsorship.amount), method="post", action="/ticket/%s/validate" % identifier)

					elif (status != 'COMPLETED' and (status == 'NEW' or user_sponsorship.amount == 0) 
							and user != None 
							and user_sponsorship.status == None or user_sponsorship.status == 'PLEDGED'):
						action = tag.form(tag.input(name="amount", type="text", size="3", value=user_sponsorship.amount), tag.input(type="submit", value="Pledge"), method="get", action="/ticket/%s/sponsor" % identifier)
					
					if action != None:
						fragment.append(" ")
						fragment.append(action)
						
				else:
					fragment.append("Error occured")
	
				add_stylesheet(req, 'htdocs/styles/gang.css')

				if not bloodhound:
					filter = Transformer('.//div[@id="ticket"]/table')
					gang_tag = tag.tr(tag.th("Bounty: ", id="h_gang"), 
							tag.td(fragment, headers="h_gang", class_="gang")) 
					stream |= filter.append(gang_tag)
				else:
					filter = Transformer('.//div[@class="description"]/')
					gang_tag = tag.table(tag.tr(tag.td("Bounty", id="h_gang"), 
							tag.td(fragment, id="vc-gang", class_="gang")), 
							class_="table table-condensed ticket-properties gang") 
					stream |= filter.before(gang_tag)

		return stream

	# IRequestHandler methods
	def match_request(self, req):
		return GANG_PATTERN.match(req.path_info) != None
	
	def process_request(self, req):
		match = GANG_PATTERN.match(req.path_info)

		if match.group('ticket'):
			ticket_id = match.group('ticket_id')
			action = match.group('ticket_action')

			if action == 'sponsor':
				amount = req.args.get('amount')
				call_gang_api('POST', '/issue/%s/sponsorships' % ticket_id, user=req.authname, amount=amount)
			elif action == 'confirm':
				pay = req.args.get('pay')
				card_number = req.args.get('card_number')
				card_date = req.args.get('card_date')
				error = "" 
				
				if pay != None:
					if not card_number or not card_date:
						error = 'Please specify card number and expiry date'
					if card_number and card_date:
						response = call_gang_api('PUT', 
								'/issue/%s/sponsorship/%s/status' % (ticket_id, req.authname), 
								status='CONFIRMED', card_number=card_number, card_date=card_date)
						if response.status_code != 200:
							error = 'API refused your payment, error code: %d' % response.status_code
						
				if pay == None or error:
					return "payment.html", {'error': error}, None
			elif action == 'validate':
				call_gang_api('PUT', '/issue/%s/sponsorship/%s/status' % (ticket_id, req.authname), 
						status='VALIDATED')
			req.redirect('/ticket/%s' % ticket_id)
		
		elif match.group('gang'):
			action = match.group('gang_action')
			if action == 'email':
				request = call_gang_api('GET', '/emails')
				if request.status_code == 200:
					emails = [Email(email) for email in request.json().get('data')]
					for email in emails:
						send_email(self.env, email.recipient, email.subject, email.body)
						call_gang_api('DELETE', '/email/%s' % email.id), 
			req.send_no_content()

	# ITicketChangeListener methods
	def ticket_created(self, ticket):
		pass

	def ticket_changed(self, ticket, comment, author, old_values):
		if 'status' in old_values:
			status = convert_status(ticket.values['status'])
			call_gang_api('PUT', '/issue/%s/status' % ticket.id, status=status)

	def ticket_deleted(self, ticket):
		pass

    # ITemplateProvider methods
	def get_templates_dirs(self):
		return [resource_filename(__name__, 'templates')]

	def get_htdocs_dirs(self):
		"""Return a list of directories with static resources (such as style
		sheets, images, etc.)

		Each item in the list must be a `(prefix, abspath)` tuple. The
		`prefix` part defines the path in the URL that requests to these
		resources are prefixed with.

		The `abspath` is the absolute path to the directory containing the
		resources on the local file system.
		"""
		return [('htdocs', resource_filename(__name__, 'htdocs'))]



class GenericNotifyEmail(NotifyEmail):
	template_name = 'email.txt'

	def __init__(self, env, recipient, body):
		NotifyEmail.__init__(self, env)
		self.recipient = recipient
		self.data = {}
		self.data['body'] = body

	def get_recipients(self, resid):
		return ([self.recipient], [])	

def send_email(env, recipient, subject, body):
	email = GenericNotifyEmail(env, recipient, body)
	email.notify('loomchild', subject)

	

