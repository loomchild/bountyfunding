# -*- coding: utf-8 -*-

from pprint import pprint

from genshi.filters import Transformer
from genshi.builder import tag

from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler, HTTPInternalError
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, add_script, add_warning, add_notice
from trac.web.api import IRequestFilter, ITemplateStreamFilter
from trac.ticket.api import ITicketChangeListener, ITicketManipulator
from trac.prefs import IPreferencePanelProvider
from trac.ticket.model import Ticket

from trac.notification import NotifyEmail

from genshi.template.text import NewTextTemplate

import requests, re
from pkg_resources import resource_filename

#from IPython import embed

# Configuration
DEFAULT_API_URL='http://localhost:5000'
DEFAULT_TOKEN = 'default'
DEFAULT_MAPPING_READY = ['new', 'accepted', 'reopened']
DEFAULT_MAPPING_STARTED = ['assigned']
DEFAULT_MAPPING_COMPLETED = ['closed']


BOUNTYFUNDING_PATTERN = re.compile("(?:/(?P<ticket>ticket)/(?P<ticket_id>[0-9]+)/(?P<ticket_action>sponsor|update_sponsorship|confirm|validate|pay))|(?:/(?P<bountyfunding>bountyfunding)/(?P<bountyfunding_action>status|email|sync))")


class Sponsorship:
	def __init__(self, dictionary={}):
		self.amount = dictionary.get('amount', 0)
		self.status = dictionary.get('status')

class Email:
	def __init__(self, dictionary):
		self.id = dictionary.get('id')
		self.recipient = dictionary.get('recipient')
		self.issue_id = dictionary.get('issue_id')
		self.body = dictionary.get('body')

class GenericNotifyEmail(NotifyEmail):
	template_name = 'email.txt'

	def __init__(self, env, recipient, body, link):
		NotifyEmail.__init__(self, env)
		self.recipient = recipient
		self.data = {
			'body': body,
			'link': link,
			'project_name': env.project_name,
			'project_url': env.project_url or self.env.abs_href(),
		}

	def get_recipients(self, resid):
		return ([self.recipient], [])	

def sum_amounts(sponsorships, statuses=None):
	if statuses != None:
		sponsorships = [s for s in sponsorships if s.status in statuses]
	total_amount = sum(map(lambda s: s.amount, sponsorships))
	return total_amount



class BountyFundingPlugin(Component):
	implements(ITemplateStreamFilter, IRequestFilter, IRequestHandler, ITemplateProvider, ITicketChangeListener, ITicketManipulator, IPreferencePanelProvider)

	def __init__(self):
		self.configure()

	def configure(self):
		self.api_url = self.config.get('bountyfunding', 'api_url', DEFAULT_API_URL)
		self.token = self.config.get('bountyfunding', 'token', DEFAULT_TOKEN)
		
		self.status_mapping = {}
		for m in self.get_config_array(
					'bountyfunding', 'status_mapping_ready', DEFAULT_MAPPING_READY):
			self.status_mapping[m] = 'READY'
		for m in self.get_config_array(
					'bountyfunding', 'status_mapping_started', DEFAULT_MAPPING_STARTED):
			self.status_mapping[m] = 'STARTED'
		for m in self.get_config_array(
					'bountyfunding', 'status_mapping_completed', DEFAULT_MAPPING_COMPLETED):
			self.status_mapping[m] = 'COMPLETED'

	def get_config_array(self, section, option, default):
		value = self.config.get(section, option, None)
		if value != None:
			return [v.strip() for v in value.split(",")]
		else:
			return default

	def call_api(self, method, path, **kwargs):
		url = self.api_url + path
		params = kwargs
		params['token'] = self.token
		try:
			response = requests.request(method, url, params=kwargs)
		except requests.exceptions.ConnectionError:
			self.log.warn("Error connecting to BountyFunding API")
			response = None
		return response
	
	def convert_status(self, status):
		return self.status_mapping[status]
	
	def get_sponsorships(self, ticket_id):
		sponsorships = {}
		request = self.call_api('GET', '/issue/%s/sponsorships' % ticket_id)
		if request.status_code == 200:
			sponsorships = dict(map(lambda (k,v): (k, Sponsorship(v)), request.json().items()))
		return sponsorships

	#TODO: not entirely safe from race conditions, fix it
	def update_ticket(self, ticket, refresh_amount=True, author=None, comment=None):
		update = (comment != None)

		if refresh_amount:
			sponsorships = self.get_sponsorships(ticket.id)	
			amount = sum_amounts(sponsorships.values())
			if amount == 0:
				if ticket["bounty"]:
					ticket["bounty"] = None
					update = True
			else:
				amount = u"%d\u20ac" % amount
				if ticket["bounty"] != amount:
					ticket["bounty"] = amount
					update = True

		if update:
			ticket.save_changes(author, comment)
	
		return update
    
	def update_api_ticket(self, ticket):
		r = self.call_api('GET', '/issue/%s' % ticket.id)
		if r.status_code != 200:
			return False

		api_ticket = r.json()
		
		title = ticket['summary']
		status = self.convert_status(ticket['status'])
		owner = ticket['owner']
		
		changes = {}

		if title != api_ticket.get('title'):
			changes['title'] = title

		if status != api_ticket.get('status'):
			changes['status'] = status

		if owner != api_ticket.get('owner'):
			changes['owner'] = owner

		if changes:
			self.call_api('PUT', '/issue/%s' % ticket.id, **changes)
			return True

		return False

	def get_link(self, ticket_id):
		return '/ticket/%s' % ticket_id

	def send_email(self, recipient, ticket_id, body):
		ticket = Ticket(self.env, ticket_id)
		subject = self.format_email_subject(ticket)
		link = self.env.abs_href.ticket(ticket_id)

		email = GenericNotifyEmail(self.env, recipient, body, link)
		email.notify('', subject)

	def format_email_subject(self, ticket):
		template = self.config.get('notification','ticket_subject_template')
		template = NewTextTemplate(template.encode('utf8'))

		prefix = self.config.get('notification', 'smtp_subject_prefix')
		if prefix == '__default__':
			prefix = '[%s]' % self.env.project_name

		data = {
			'prefix': prefix,
			'summary': ticket['summary'],
			'ticket': ticket,
			'env': self.env,
		}

		return template.generate(**data).render('text', encoding=None).strip()

	
	# ITemplateStreamFilter methods
	def filter_stream(self, req, method, filename, stream, data):
		"""
		Quick and dirty solution - modify page on the fly to inject special field. It would be
		nicer if we can do it by creating custom field as this depends on page structure.
		"""
		#embed(header='Ticket Stream Filter')
		if filename == 'ticket.html':
			# Disable any direct bounty input
			filter = Transformer('.//input[@id="field-bounty"]')
			stream |= filter.attr("disabled", "disabled")
			
			ticket = data.get('ticket')
			if ticket and ticket.exists:
				identifier = ticket.id
				user = req.authname if req.authname != 'anonymous' else None
				request = self.call_api('GET', '/issue/%s' % identifier)
				fragment = tag()
				sponsorships = {}
				status = self.convert_status(ticket.values['status'])
				owner = ticket.values['owner']
				tooltip = None
				if request != None and (request.status_code == 200 or request.status_code == 404):
					sponsorships = self.get_sponsorships(identifier)
					
					pledged_amount = sum_amounts(sponsorships.values())
					user_sponsorship = sponsorships.get(user, Sponsorship())

					# Bounty
					tooltip = u"Pledged: %d\u20ac" % pledged_amount
					
					if status == 'STARTED' or status == 'COMPLETED':
						confirmed_amount = sum_amounts(sponsorships.values(), ('CONFIRMED', 'VALIDATED', 'REJECTED', 'TRANSFERRED', 'REFUNDED'))
						tooltip += u" \nConfirmed: %d\u20ac" % confirmed_amount
					if status == 'COMPLETED':
						validated_amount = sum_amounts(sponsorships.values(), 'VALIDATED')
						tooltip += u" \nValidated: %d\u20ac" % validated_amount
					
					# Action
					action = None
					if (((status == 'STARTED' or status == 'COMPLETED') 
							and user_sponsorship.status == 'PLEDGED') 
						or (status == 'STARTED' and user != None and user != owner
							and user_sponsorship.status == None)):
						response = self.call_api('GET', '/config/payment_gateways')
						gateways = response.json().get('gateways')
						gateway_tags = []
						if 'DUMMY' in gateways:
							gateway_tags.append(tag.input(type="submit", value="Payment Card", name='DUMMY'))
						if 'PAYPAL_STANDARD' in gateways:
							gateway_tags.append(tag.input(type="submit", value="PayPal", name='PAYPAL_STANDARD'))
						if 'PAYPAL_ADAPTIVE' in gateways:
							gateway_tags.append(tag.input(type="submit", value="PayPal", name='PAYPAL_ADAPTIVE'))
						if user_sponsorship.status == 'PLEDGED':
							action = tag.form(
								tag.input(type="button", name="confirm", value=u"Confirm %d\u20ac" % user_sponsorship.amount, id="confirm-button"), 
								tag.span(gateway_tags, id="confirm-options"), 
								tag.input(type="submit", name="cancel", value="Cancel"), 
								method="post", action=req.href.ticket(identifier, "confirm"))
						else:
							#TODO: should be separate action
							action = tag.form(
								tag.input(name="amount", type="text", size="3", value="0", pattern="[0-9]*", title="money amount"), 
								tag.input(type="button", value="Pledge & Confirm", id="confirm-button"), 
								tag.span(gateway_tags, id="confirm-options"), 
								method="post", action=req.href.ticket(identifier, "confirm"))

					elif status == 'COMPLETED' and user_sponsorship.status in ('CONFIRMED', 'REJECTED', 'VALIDATED'):
						action = tag.form(method="post", action=req.href.ticket(identifier, "validate"))
						if user_sponsorship.status == 'CONFIRMED' or user_sponsorship.status == 'REJECTED':
							action.append(tag.input(type="submit", name='validate', value=u"Validate %d\u20ac" % user_sponsorship.amount))
						if user_sponsorship.status == 'CONFIRMED' or user_sponsorship.status == 'VALIDATED':
							action.append(tag.input(type="submit", name='reject', value="Reject"))
					elif (status == 'READY' and user != None):
						if user_sponsorship.status == None:
							action = tag.form(tag.input(name="amount", type="text", size="3", value=user_sponsorship.amount, pattern="[0-9]*", title="money amount"), tag.input(type="submit", value="Pledge"), method="post", action=req.href.ticket(identifier, "sponsor"))
						elif user_sponsorship.status == 'PLEDGED':
							action = tag.form(tag.input(name="amount", type="text", size=3, value=user_sponsorship.amount, pattern="[0-9]*", title="money amount"), tag.input(type="submit", name="update", value="Update"), tag.input(type="submit", name="cancel", value="Cancel"), method="post", action=req.href.ticket(identifier, "update_sponsorship"))
					
					elif (user == None):
						action = tag.span(u"\u00A0", tag.a("Login", href=req.href.login()), " or ", tag.a("Register", href=req.href.register()), " to sponsor")
					
					if action != None:
						fragment.append(" ")
						fragment.append(action)
						
				else:
					error = "Connection error"
					if request:
						error = request.json().get("error", "Unknown error")
					fragment.append(tag.span("[API Error]", title=error))
	
				#chrome = Chrome(self.env)
				#chrome.add_jquery_ui(req)
				
				add_stylesheet(req, 'htdocs/styles/bountyfunding.css')
				add_script(req, 'htdocs/scripts/bountyfunding.js')

				if tooltip != None:
					filter = Transformer('.//td[@headers="h_bounty"]/text()')
					stream |= filter.wrap(tag.span(title=tooltip))

				filter = Transformer('.//td[@headers="h_bounty"]')
				stream |= filter.attr("class", "bountyfunding")
				stream |= filter.append(fragment)
				
		return stream

	
	# IRequestFilter methods
	def pre_process_request(self, req, handler):
		return handler

	def post_process_request(self, req, template, data, content_type):
		#if template == 'ticket.html':
		#	ticket = data.get('ticket')
		#	if ticket and ticket.exists:
		#		ticket.values['bounty'] = '100'
		return template, data, content_type

	
	# IRequestHandler methods
	def match_request(self, req):
		return BOUNTYFUNDING_PATTERN.match(req.path_info) != None
	
	def process_request(self, req):
		match = BOUNTYFUNDING_PATTERN.match(req.path_info)

		if match.group('ticket'):
			ticket_id = match.group('ticket_id')
			action = match.group('ticket_action')
			user = req.authname
			ticket = Ticket(self.env, ticket_id)
			ticket_title = ticket['summary']
			ticket_link = self.get_link(ticket_id)
			ticket_owner = ticket['owner']
			ticket_status = self.convert_status(ticket['status'])

			if action == 'sponsor':
				amount = req.args.get('amount')
				if self.call_api('GET', '/issue/%s' % ticket_id).status_code == 404:
					self.call_api('POST', '/issues', ref=ticket_id, status=ticket_status, title=ticket_title, link=ticket_link, owner=ticket_owner)
				response = self.call_api('POST', '/issue/%s/sponsorships' % ticket_id, user=user, amount=amount)
				if response.status_code != 200:
					add_warning(req, "Unable to pledge - %s" % response.json().get('error', ''))
				else:
					self.update_ticket(ticket, True, user)
			if action == 'update_sponsorship':
				if req.args.get('update'):
					amount = req.args.get('amount')
					response = self.call_api('PUT', '/issue/%s/sponsorship/%s' % (ticket_id, user), amount=amount)
					if response.status_code != 200:
						add_warning(req, "Unable to pledge - %s" % response.json().get('error', ''))
					else:
						self.update_ticket(ticket, True, user)
				elif req.args.get('cancel'):
					response = self.call_api('DELETE', '/issue/%s/sponsorship/%s' % (ticket_id, user))
					if response.status_code != 200:
						add_warning(req, "Unable to cancel pledge - %s" % response.json().get('error', ''))
					else:
						self.update_ticket(ticket, True, user)
			elif action == 'confirm':
				if req.args.get('cancel'):
					response = self.call_api('DELETE', '/issue/%s/sponsorship/%s' % (ticket_id, user))
					if response.status_code != 200:
						add_warning(req, "Unable to cancel pledge - %s" % response.json().get('error', ''))
					else:
						self.update_ticket(ticket, True, user)
				else:
					if req.args.get('DUMMY'):
						gateway = 'DUMMY'
					elif req.args.get('PAYPAL_STANDARD'):
						gateway = 'PAYPAL_STANDARD'
					elif req.args.get('PAYPAL_ADAPTIVE'):
						gateway = 'PAYPAL_ADAPTIVE'
					else:
						#TODO: raise exception instead
						gateway = None
					
					response = self.call_api('GET', '/issue/%s/sponsorship/%s' % (ticket_id, user))
					if response.status_code == 404:
						# Security: can't sponsor not started tickets
						if ticket_status != 'STARTED':
							#TODO: prevent confirming, exception would be much nicer
							gateway = None
						else:
							amount = req.args.get('amount')
							if self.call_api('GET', '/issue/%s' % ticket_id).status_code == 404:
								self.call_api('POST', '/issues', ref=ticket_id, status=ticket_status, title=ticket_title, link=ticket_link, owner=ticket_owner)
							response = self.call_api('POST', '/issue/%s/sponsorships' % ticket_id, user=user, amount=amount)
							if response.status_code != 200:
								add_warning(req, "Unable to pledge - %s" % response.json().get('error', ''))
								#TODO: prevent confirming, exception would be much nicer
								gateway = None

					if gateway == 'DUMMY':
						pay = req.args.get('pay')
						card_number = req.args.get('card_number')
						card_date = req.args.get('card_date')
						error = "" 
					
						if pay != None:
							if not card_number or not card_date:
								error = 'Please specify card number and expiry date'
							if card_number and card_date:
								response = self.call_api('POST', 
										'/issue/%s/sponsorship/%s/payments' % (ticket_id, user), 
										gateway='DUMMY')
								if response.status_code != 200:
									error = 'API cannot create plain payment'
								response = self.call_api('PUT', 
										'/issue/%s/sponsorship/%s/payment' % (ticket_id, user), 
										status='CONFIRMED', card_number=card_number, card_date=card_date)
								if response.status_code != 200:
									error = 'API refused your plain payment'
								else:
									self.update_ticket(ticket, True, user, 'Confirmed sponsorship.')
								
						if pay == None or error:
							return "payment.html", {'error': error}, None
		
					elif gateway == 'PAYPAL_STANDARD' or gateway == 'PAYPAL_ADAPTIVE':
						return_url = req.abs_href('ticket', ticket_id, 'pay')
						response = self.call_api('POST', 
								'/issue/%s/sponsorship/%s/payments' % (ticket_id, user), 
								gateway=gateway, return_url=return_url)
						if response.status_code == 200:
							response = self.call_api('GET', 
									'/issue/%s/sponsorship/%s/payment' % (ticket_id, user))
							if response.status_code == 200:
								redirect_url = response.json().get('url')
								req.redirect(redirect_url)
							else:
								error = 'API cannot retrieve created PayPal payment'
						else:
							error = 'API cannot create PayPal payment'
						add_warning(req, error)
			
			elif action == 'pay':
				args = dict(req.args)
				args['status'] = 'CONFIRMED'
				response = self.call_api('PUT', '/issue/%s/sponsorship/%s/payment' % (ticket_id, user), 
						**args)
				if response.status_code == 200:
					self.update_ticket(ticket, True, user, 'Confirmed sponsorship.')
					add_notice(req, "Thank you for your payment. Your transaction has been completed, and a receipt for your purchase has been emailed to you.")
			elif action == 'validate':
				if req.args.get('validate'):
					response = self.call_api('PUT', '/issue/%s/sponsorship/%s' % (ticket_id, user), 
						status='VALIDATED')
					if response.status_code == 200:
						self.update_ticket(ticket, True, user, 'Validated sponsorship.')
				elif req.args.get('reject'):
					response = self.call_api('PUT', '/issue/%s/sponsorship/%s' % (ticket_id, user), 
						status='REJECTED')
					if response.status_code == 200:
						self.update_ticket(ticket, True, user, 'Rejected sponsorship.')


			req.redirect(req.href.ticket(ticket_id))
		
		elif match.group('bountyfunding'):
			action = match.group('bountyfunding_action')
			if action == 'email':
				request = self.call_api('GET', '/emails')
				if request.status_code == 200:
					emails = [Email(email) for email in request.json().get('data')]
					for email in emails:
						self.send_email(email.recipient, int(email.issue_id), email.body)
						self.call_api('DELETE', '/email/%s' % email.id), 
				req.send_no_content()
			if action == 'status':
				request = self.call_api('GET', '/version')
				if request == None:
					raise HTTPInternalError('Unable to connect to BountyFunding API')
				elif request.status_code == 403:
					raise HTTPInternalError('Not permitted to connect to BountyFunding API, check token')
				elif request.status_code != 200:
					raise HTTPInternalError('Invalid HTTP status code %s when connecting to'
							' BountyFunding API' % request.status_code)
				else:
					try:
						version = request.json().get('version')
						return "status.html", {'version': version}, None
					except (ValueError, KeyError):
						raise HTTPInternalError('Invalid response body from BountyFunding API')
						
			if action == 'sync':
				#TODO: optimize by calling /issues, setting amount to 0 if not found
				updated_ids = set()
				user = req.authname
				if 'TICKET_ADMIN' in req.perm:
					for row in self.env.db_query("SELECT id from ticket ORDER BY id ASC"):
						ticket_id = row[0]
						ticket = Ticket(self.env, ticket_id)
						if self.update_ticket(ticket, True, user):
							updated_ids.add(ticket_id)
						if self.update_api_ticket(ticket):
							updated_ids.add(ticket_id)
				else:		
					add_warning(req, "You are not permitted to sync")

				return "sync.html", {"ids": sorted(updated_ids)}, None


	# ITicketChangeListener methods
	def ticket_created(self, ticket):
		pass

	def ticket_changed(self, ticket, comment, author, old_values):
		changes = {}
	
		if 'status' in old_values:
			changes['status'] = self.convert_status(ticket.values['status'])
	
		if 'summary' in old_values:
			changes['title'] = ticket['summary']

		if 'owner' in old_values:
			changes['owner'] = ticket['owner']

		if changes: 
			# Ignore error 404
			self.call_api('PUT', '/issue/%s' % ticket.id, **changes)

	def ticket_deleted(self, ticket):
		pass


	# ITicketManipulator methods
	def prepare_ticket(self, req, ticket, fields, actions):
		pass
   
	def validate_ticket(self, req, ticket):
		if ticket.exists:
			old_ticket = Ticket(self.env, ticket.id)
			if ticket['bounty'] != old_ticket['bounty']:
				return [('bounty', 'Bounty cannot be changed')]
		else:
			if ticket['bounty']:
				return [('bounty', 'Bounty cannot be set')]
		return []


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


	# IPreferencePanelProvider methods

	def get_preference_panels(self, req):
		#TODO: this should probably be only visible when using adaptive payments
		yield ('bountyfunding', 'BountyFunding')

	def render_preference_panel(self, req, panel):
		user = req.authname
		if req.method == 'POST':
			paypal_email = req.args.get('bountyfunding_paypal_email')
			if paypal_email != None:
				#TODO: perform some validation if possible - see what FreedomSponsors is doing
				request = self.call_api('PUT', '/user/%s' % user, paypal_email=paypal_email)
				if request and request.status_code == 200:
					add_notice(req, 'Your BountyFunding settings have been been saved.')
				else:
					add_warning(req, 'Error saving BountyFunding settings.')

			req.redirect(req.href.prefs(panel or None))
		
		paypal_email = ''

		request = self.call_api('GET', '/user/%s' % user)
		if request and request.status_code == 200:
			paypal_email = request.json().get('paypal_email', '')

		return 'bountyfunding_prefs.html', {
			'bountyfunding_paypal_email': paypal_email,
		}
