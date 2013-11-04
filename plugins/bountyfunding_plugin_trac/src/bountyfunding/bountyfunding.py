from pprint import pprint

from genshi.filters import Transformer
from genshi.builder import tag

from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler, HTTPInternalError
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, add_script, add_warning
from trac.web.api import ITemplateStreamFilter
from trac.ticket.api import ITicketChangeListener

from trac.notification import NotifyEmail

import requests, re
from pkg_resources import resource_filename


API_URL='http://localhost:5000'
BOUNTYFUNDING_PATTERN = re.compile("(?:/(?P<ticket>ticket)/(?P<ticket_id>[0-9]+)/(?P<ticket_action>sponsor|update_sponsorship|confirm|validate|pay))|(?:/(?P<bountyfunding>bountyfunding)/(?P<bountyfunding_action>status|email))")


def call_api(method, path, **kwargs):
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


class BountyFundingPlugin(Component):
	implements(ITemplateStreamFilter, IRequestHandler, ITemplateProvider, ITicketChangeListener)

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
				request = call_api('GET', '/issue/%s' % identifier)
				fragment = tag()
				sponsorships = {}
				status = convert_status(ticket.values['status'])
				owner = ticket.values['owner']
				if request.status_code == 200 or request.status_code == 404:
					
					sponsorships = {}
					request = call_api('GET', '/issue/%s/sponsorships' % identifier)
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
						action = tag.form(tag.input(type="button", value=u"Confirm %d\u20ac" % user_sponsorship.amount, id="confirm-button"), tag.span(tag.input(type="button", value="Cancel", id="confirm-cancel"), tag.input(type="submit", value="Payment Card", name='plain'), tag.input(type="submit", value="PayPal", name='paypal'), id="confirm-options"), method="post", action="/ticket/%s/confirm" % identifier)

					elif status == 'COMPLETED' and user_sponsorship.status == 'CONFIRMED':
						action = tag.form(tag.input(type="submit", name='accept', value=u"Validate %d\u20ac" % user_sponsorship.amount), method="post", action="/ticket/%s/validate" % identifier)

					elif (status != 'COMPLETED' and (status == 'NEW' or user_sponsorship.amount == 0) 
							and user != None):
						if user_sponsorship.status == None:
							action = tag.form(tag.input(name="amount", type="text", size="3", value=user_sponsorship.amount), tag.input(type="submit", value="Pledge"), method="post", action="/ticket/%s/sponsor" % identifier)
						elif user_sponsorship.status == 'PLEDGED':
							action = tag.form(tag.input(name="amount", type="text", size="3", value=user_sponsorship.amount), tag.input(type="submit", name="update", value="Update"), tag.input(type="submit", name="cancel", value="Cancel"), method="post", action="/ticket/%s/update_sponsorship" % identifier)
					
					if action != None:
						fragment.append(" ")
						fragment.append(action)
						
				else:
					fragment.append("Error occured")
	
				#chrome = Chrome(self.env)
				#chrome.add_jquery_ui(req)
				
				add_stylesheet(req, 'htdocs/styles/bountyfunding.css')
				add_script(req, 'htdocs/scripts/bountyfunding.js')

				filter = Transformer('.//table[@class="properties"]	')
				bountyfunding_tag = tag.tr(tag.th("Bounty: ", id="h_bountyfunding"), 
						tag.td(fragment, headers="h_bountyfunding", class_="bountyfunding")) 
				stream |= filter.append(bountyfunding_tag)
		return stream

	# IRequestHandler methods
	def match_request(self, req):
		return BOUNTYFUNDING_PATTERN.match(req.path_info) != None
	
	def process_request(self, req):
		match = BOUNTYFUNDING_PATTERN.match(req.path_info)

		if match.group('ticket'):
			ticket_id = match.group('ticket_id')
			action = match.group('ticket_action')

			if action == 'sponsor':
				amount = req.args.get('amount')
				response = call_api('POST', '/issue/%s/sponsorships' % ticket_id, user=req.authname, amount=amount)
				if response.status_code != 200:
					add_warning(req, "Unable to pledge - %s" % response.json().get('error', ''))
			if action == 'update_sponsorship':
				if req.args.get('update'):
					amount = req.args.get('amount')
					response = call_api('PUT', '/issue/%s/sponsorship/%s' % (ticket_id, req.authname), amount=amount)
					if response.status_code != 200:
						add_warning(req, "Unable to pledge - %s" % response.json().get('error', ''))
				elif req.args.get('cancel'):
					call_api('DELETE', '/issue/%s/sponsorship/%s' % (ticket_id, req.authname))
			elif action == 'confirm':
				if req.args.get('plain'):
					gateway = 'PLAIN'
				elif req.args.get('paypal'):
					gateway = 'PAYPAL'

				if gateway == 'PLAIN':
					pay = req.args.get('pay')
					card_number = req.args.get('card_number')
					card_date = req.args.get('card_date')
					error = "" 
				
					if pay != None:
						if not card_number or not card_date:
							error = 'Please specify card number and expiry date'
						if card_number and card_date:
							response = call_api('POST', 
									'/issue/%s/sponsorship/%s/payments' % (ticket_id, req.authname), 
									gateway='PLAIN')
							if response.status_code != 200:
								error = 'API cannot create plain payment'
							response = call_api('PUT', 
									'/issue/%s/sponsorship/%s/payment' % (ticket_id, req.authname), 
									status='CONFIRMED', card_number=card_number, card_date=card_date)
							if response.status_code != 200:
								error = 'API refused your plain payment'
							
					if pay == None or error:
						return "payment.html", {'error': error}, None
	
				elif gateway == 'PAYPAL':
					return_url = req.abs_href('ticket', ticket_id, 'pay')
					response = call_api('POST', 
							'/issue/%s/sponsorship/%s/payments' % (ticket_id, req.authname), 
							gateway='PAYPAL', return_url=return_url)
					if response.status_code == 200:
						response = call_api('GET', 
								'/issue/%s/sponsorship/%s/payment' % (ticket_id, req.authname), 
								gateway='PAYPAL')
						if response.status_code == 200:
							redirect_url = response.json().get('url')
							req.redirect(redirect_url)
						else:
							error = 'API cannot retrieve created paypal payment'
					else:
						error = 'API cannot create paypal payment'
			
			elif action == 'pay':
				payer_id = req.args.get('PayerID')
				call_api('PUT', '/issue/%s/sponsorship/%s/payment' % (ticket_id, req.authname), 
						status='CONFIRMED', payer_id=payer_id)
			elif action == 'validate':
				call_api('PUT', '/issue/%s/sponsorship/%s' % (ticket_id, req.authname), 
						status='VALIDATED')
			req.redirect('/ticket/%s' % ticket_id)
		
		elif match.group('bountyfunding'):
			action = match.group('bountyfunding_action')
			if action == 'email':
				request = call_api('GET', '/emails')
				if request.status_code == 200:
					emails = [Email(email) for email in request.json().get('data')]
					for email in emails:
						send_email(self.env, email.recipient, email.subject, email.body)
						call_api('DELETE', '/email/%s' % email.id), 
				req.send_no_content()
			if action == 'status':
				try:
					request = call_api('GET', '/version')
				except requests.ConnectionError:
					raise HTTPInternalError('Unable to connect to API')
				if request.status_code != 200:
					raise HTTPInternalError('Invalid status code when connection to API' 
							% request.status_code)
				else:
					return "status.html", {'version': request.json().get('version')}, None

	# ITicketChangeListener methods
	def ticket_created(self, ticket):
		pass

	def ticket_changed(self, ticket, comment, author, old_values):
		if 'status' in old_values:
			status = convert_status(ticket.values['status'])
			call_api('PUT', '/issue/%s' % ticket.id, status=status)

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

	

