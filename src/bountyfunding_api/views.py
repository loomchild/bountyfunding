from bountyfunding_api import app
from flask import Flask, url_for, render_template, make_response, redirect, abort, jsonify, request, g
from models import db, Issue, User, Sponsorship, Email, Payment, Change
from const import IssueStatus, SponsorshipStatus, PaymentStatus, PaymentGateway
from pprint import pprint
import paypal_rest
import paypal_standard
from config import config
import re, requests, threading

DEFAULT_PROJECT_ID = 1
DATE_PATTERN = re.compile('^(0?[1-9]|1[012])/[0-9][0-9]$')

NOTIFY_INTERVAL = 5


@app.route('/version', methods=['GET'])
def status():
	return jsonify(version=config.VERSION)

@app.route("/issues", methods=['GET'])
def get_issues():
	issues = retrieve_issues(g.project_id)
	issues = dict(map(lambda i: (i.issue_ref, {}), issues))
	response = jsonify(issues)
	return response

@app.route("/issue/<issue_ref>", methods=['GET'])
def get_issue(issue_ref):
	issue = retrieve_issue(g.project_id, issue_ref)
	if issue != None:
		response = jsonify()
	else:
		response = jsonify(error='Issue not found'), 404
	return response

@app.route("/issue/<issue_ref>", methods=['PUT'])
def update_status(issue_ref):
	status = IssueStatus.from_string(request.values.get('status'))

	issue = retrieve_issue(g.project_id, issue_ref)

	if issue != None:
		if status == IssueStatus.STARTED:
			body = 'The task you have sponsored has been started. Please deposit the promised amount. To do that please go to project issue tracker, log in, find this issue and select Confirm.'
			notify_sponsors(g.project_id, issue.issue_id, SponsorshipStatus.PLEDGED, body)
		elif status == IssueStatus.COMPLETED:
			body_confirmed = 'The task you have sponsored has been completed by the developer. Please validate it. To do that please go to project issue tracker, log in, find an issue and select Validate.'
			notify_sponsors(g.project_id, issue.issue_id, SponsorshipStatus.CONFIRMED, body_confirmed)
			
			body_pledged = 'The task you have sponsored has been completed by the developer. Please deposit the promised amout and validate it. To do that please go to project issue tracker, log in, find an issue and select Confirm and then Validate.'
			notify_sponsors(g.project_id, issue.issue_id, SponsorshipStatus.PLEDGED, body_pledged)
		
		else:
			return jsonify(error="Unknown status"), 400

	return jsonify(message='OK')

@app.route("/issue/<issue_ref>/sponsorships", methods=['GET'])
def get_sponsorships(issue_ref):
	sponsorships = []
	issue = retrieve_issue(g.project_id, issue_ref)

	if issue != None:
		sponsorships = retrieve_all_sponsorships(issue.issue_id)
		sponsorships = dict(map(\
				lambda s: (s.user.name, \
				{'amount': s.amount, 'status': SponsorshipStatus.to_string(s.status)}),\
				sponsorships))
		response = jsonify(sponsorships)
	else:
		response = jsonify(error='Issue not found'), 404
	return response

@app.route("/issue/<issue_ref>/sponsorships", methods=['POST'])
def post_sponsorship(issue_ref):
	user_name = request.values.get('user')
	amount = int(request.values.get('amount'))

	check_pledge_amount(g.project_id, amount)

	issue = retrieve_create_issue(g.project_id, issue_ref)
	user = retrieve_create_user(g.project_id, user_name)
	
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
	if sponsorship != None:
		return jsonify(error="Sponsorship already exists"), 409

	sponsorship = Sponsorship(g.project_id, issue.issue_id, user.user_id)
	
	sponsorship.amount = amount
	
	db.session.add(sponsorship)
	db.session.commit()

	response = jsonify(message='Sponsorship updated')
	return response

@app.route("/issue/<issue_ref>/sponsorship/<user_name>", methods=['GET'])
def get_sponsorship(issue_ref, user_name):
	issue = retrieve_issue(g.project_id, issue_ref)
	user = retrieve_user(g.project_id, user_name)

	if issue == None:
		response = jsonify(error='Issue not found'), 404

	elif user == None:
		response = jsonify(error='User not found'), 404

	else:
		sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
		if sponsorship == None:
			response = jsonify(error='Sponsorship not found'), 404
		else:
			status = SponsorshipStatus.to_string(sponsorship.status)
			response = jsonify(status=status)
	
	return response

@app.route("/issue/<issue_ref>/sponsorship/<user_name>", methods=['DELETE'])
def delete_sponsorship(issue_ref, user_name):
	issue = retrieve_issue(g.project_id, issue_ref)
	user = retrieve_user(g.project_id, user_name)

	if issue == None:
		response = jsonify(error='Issue not found'), 404

	elif user == None:
		response = jsonify(error='User not found'), 404

	else:
		sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
		if sponsorship.status != SponsorshipStatus.PLEDGED:
			return jsonify(error='Can only delete sponsorhip in PLEDGED status'), 403

		delete_sponsorship(issue.issue_id, user.user_id)
		response = jsonify(message="Sponsorship deleted")
	
	return response

@app.route("/issue/<issue_ref>/sponsorship/<user_name>", methods=['PUT'])
def update_sponsorship(issue_ref, user_name):
	status_string = request.values.get('status')
	status = SponsorshipStatus.from_string(status_string) 
	amount_string = request.values.get('amount')

	issue = retrieve_issue(g.project_id, issue_ref)
	user = retrieve_user(g.project_id, user_name)
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)

	if status == None and amount_string == None:
		return jsonify(error="Nothing to update"), 400

	if status != None:
		if status == SponsorshipStatus.PLEDGED:
			return jsonify(error='Cannot change state to PLEDGED'), 400
		elif status == SponsorshipStatus.CONFIRMED:
			return jsonify(error='Confirm sponsorship by confirming the payment'), 400
		elif status == sponsorship.status:
			return jsonify(error='Status already set'), 403
		elif status == SponsorshipStatus.VALIDATED:
			if (sponsorship.status != SponsorshipStatus.CONFIRMED
					and sponsorship.status != SponsorshipStatus.REJECTED):
				return jsonify(error='Can only validate confirmed sponsorship'), 403
			admin = retrieve_create_user(g.project_id, config.ADMIN)
			body = 'User %s has validated his/her sponsorship. Please transfer the money to the developer.'% user_name
			create_email(g.project_id, admin.user_id, issue.issue_id, body)
		elif status == SponsorshipStatus.TRANSFERRED:
			if sponsorship.status != SponsorshipStatus.VALIDATED:
				return jsonify(error='Can only transfer when sponsorship is validated'), 403
		elif status == SponsorshipStatus.REJECTED:
			if (sponsorship.status != SponsorshipStatus.CONFIRMED 
					and sponsorship.status != SponsorshipStatus.VALIDATED):
				return jsonify(error='Can only reject confirmed sponsorship'), 403
			admin = retrieve_create_user(g.project_id, config.ADMIN)
			body = 'User %s has rejected his/her sponsorship. Please refund the money to the user.'% user_name
			create_email(g.project_id, admin.user_id, issue.issue_id, body)
		elif status == SponsorshipStatus.REFUNDED:
			if sponsorship.status != SponsorshipStatus.REJECTED:
				return jsonify(error='Can only refund rejected sponsorship'), 403
		else:
			return jsonify(error='Invalid status: %s' % status_string), 400

		sponsorship.status = status

	if amount_string != None:
		if sponsorship.status != SponsorshipStatus.PLEDGED:
			return jsonify(error='Can only change amount in PLEDGED state'), 403
		try:
			amount = int(amount_string)
		except ValueError:
			return jsonify(error="amount is not a number"), 400
		check_pledge_amount(g.project_id, amount)

		sponsorship.amount = amount

	db.session.add(sponsorship)
	db.session.commit()

	return jsonify(message='Sponsorship updated')

@app.route("/issue/<issue_ref>/sponsorship/<user_name>/payment", methods=['GET'])
def get_payment(issue_ref, user_name):
	issue = retrieve_issue(g.project_id, issue_ref)
	user = retrieve_user(g.project_id, user_name)
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)

	payment = retrieve_last_payment(sponsorship.sponsorship_id)

	if payment != None:
		gateway = PaymentGateway.to_string(payment.gateway)
		status = PaymentStatus.to_string(payment.status)
		response = jsonify(gateway=gateway, url=payment.url, status=status)
	else:
		response = jsonify(error='Payment not found'), 404
	
	return response

@app.route("/issue/<issue_ref>/sponsorship/<user_name>/payment", methods=['PUT'])
def update_payment(issue_ref, user_name):
	status = PaymentStatus.from_string(request.values.get('status')) 
	if status != PaymentStatus.CONFIRMED:
		return jsonify(error='You can only change the status to CONFIRMED'), 403
	
	issue = retrieve_issue(g.project_id, issue_ref)
	user = retrieve_user(g.project_id, user_name)
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)

	payment = retrieve_last_payment(sponsorship.sponsorship_id)

	if payment != None:
		if payment.status == status:
			return jsonify(error='Payment already confirmed'), 403
		if payment.gateway == PaymentGateway.PLAIN:
			card_number = request.values.get('card_number')
			card_date = request.values.get('card_date')
			if card_number != '4111111111111111' or DATE_PATTERN.match(card_date) == None:
				return jsonify(error='Invalid card details'), 403
		elif payment.gateway == PaymentGateway.PAYPAL_REST:
			approved = paypal_rest.process_payment(g.project_id, sponsorship, payment, request.values)
			if not approved:
				return jsonify(error='Payment not confirmed by PayPal'), 403
		elif payment.gateway == PaymentGateway.PAYPAL_STANDARD:
			approved = paypal_standard.process_payment(g.project_id, sponsorship, payment, request.values)
			if not approved:
				return jsonify(error='Payment not confirmed by PayPal'), 403
		else:
			return jsonify(error='Unknown gateway'), 400

		payment.status = status
		db.session.add(payment)
		sponsorship.status = SponsorshipStatus.CONFIRMED
		db.session.add(sponsorship)
		db.session.commit()
		response = jsonify(message='Payment updated')
	else:
		response = jsonify(error='Payment not found'), 404
	
	return response

@app.route("/issue/<issue_ref>/sponsorship/<user_name>/payments", methods=['POST'])
def create_payment(issue_ref, user_name):
	gateway = PaymentGateway.from_string(request.values.get('gateway')) 
	if gateway not in config.PAYMENT_GATEWAYS:
		return jsonify(error="Payment gateway not accepted"), 400

	return_url = request.values.get('return_url')
	
	issue = retrieve_issue(g.project_id, issue_ref)
	user = retrieve_user(g.project_id, user_name)
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
	
	if sponsorship.status != SponsorshipStatus.PLEDGED:
		return jsonify(error="You can only create payment for PLEDGED sponsorship"), 403

	if gateway == PaymentGateway.PLAIN:
		payment = Payment(g.project_id, sponsorship.sponsorship_id, gateway)
	elif gateway == PaymentGateway.PAYPAL_REST:
		if not return_url:
			return jsonify(error='return_url cannot be blank'), 400
		payment = paypal_rest.create_payment(g.project_id, sponsorship, return_url)
	elif gateway == PaymentGateway.PAYPAL_STANDARD:
		if not return_url:
			return jsonify(error='return_url cannot be blank'), 400
		payment = paypal_standard.create_payment(g.project_id, sponsorship, return_url)
	else:
		return jsonify(error='Unknown gateway'), 400

	db.session.add(payment)
	db.session.commit()
	
	response = jsonify(message='Payment created')
	return response


@app.route('/emails', methods=['GET'])
def get_emails():
	emails = Email.query.all()

	response = []
	for email in emails:
		response.append({'id': email.email_id, 'recipient':email.user.name, 'issue_id':email.issue.issue_ref, 'body':email.body})
		
	response = jsonify(data=response)
	return response 

@app.route('/email/<email_id>', methods=['DELETE'])
def delete_email(email_id):
	email = Email.query.get(email_id)

	if email != None:
		db.session.delete(email)
		db.session.commit()
		response = jsonify(message='Email deleted')
	else:
		response = jsonify(error='Email not found'), 404
	
	return response

@app.route('/', methods=['DELETE'])
def delete_project():
	project_id = g.project_id
	if project_id >= 0:
		return jsonify(error="You can't delete this project"), 403

	Payment.query.filter_by(project_id=project_id).delete()
	Sponsorship.query.filter_by(project_id=project_id).delete()
	User.query.filter_by(project_id=project_id).delete()
	Issue.query.filter_by(project_id=project_id).delete()
	Email.query.filter_by(project_id=project_id).delete()
	db.session.commit()

	return jsonify(message="Project deleted")


@app.route('/config/payment_gateways', methods=['GET'])
def get_config_payment_gateways():
	gateways = [PaymentGateway.to_string(pg) for pg in config[g.project_id].PAYMENT_GATEWAYS]
	return jsonify(gateways=gateways)


# Order of these two functions is important - first one needs to be executed
# before the second, because I need project_id to log the change
# http://t27668.web-flask-general.webdiscuss.info/priority-for-before-request-t27668.html

@app.before_request
def check_access_and_set_project():
	at = request.values.get('at')
	if at:
		project_id = int(at)
	else:
		project_id = DEFAULT_PROJECT_ID
	g.project_id = project_id

@app.before_request
def log_change():
	if request.method == 'POST' or request.method == 'PUT' or request.method == 'DELETE':
		arguments = ", ".join(map(lambda (k, v): '%s:%s' % (k, v),\
				sorted(request.values.iteritems(True))))
		create_change(g.project_id, request.method, request.path, arguments)


@app.before_first_request
def init():
	# For in-memory DB need to initialize memory database in the same thread
	if config.DATABASE_CREATE:
		if not config.DATABASE_IN_MEMORY:
			print "Creating database in %s" % config.DATABASE_URL
		db.create_all()
	
	# Multiple threads do not work with memory database
	if not config.DATABASE_IN_MEMORY:
		notify()


class APIException(Exception):
	def __init__(self, message="", status_code=400):
		self.message = message
		self.status_code = status_code

@app.errorhandler(APIException)
def handle_api_exception(exception):
    return jsonify(error=exception.message), exception.status_code


def retrieve_issues(project_id):
	issues = Issue.query.filter_by(project_id=project_id).all()
	return issues

def retrieve_issue(project_id, issue_ref):
	issue = Issue.query.filter_by(project_id=project_id, issue_ref=issue_ref).first()
	return issue

def retrieve_create_issue(project_id, issue_ref):
	issue = retrieve_issue(project_id, issue_ref)
	if issue == None:
		issue = Issue(project_id=project_id, issue_ref=issue_ref)
		db.session.add(issue)
		db.session.commit()
	return issue

def retrieve_user(project_id, name):
	user = User.query.filter_by(project_id=project_id, name=name).first()
	return user

def retrieve_create_user(project_id, name):
	user = retrieve_user(project_id, name)
	if user == None:
		user = User(project_id=project_id, name=name)
		db.session.add(user)
		db.session.commit()
	return user

def retrieve_sponsorship(issue_id, user_id):
	sponsorship = Sponsorship.query.filter_by(issue_id=issue_id, user_id=user_id).first()
	return sponsorship

def retrieve_all_sponsorships(issue_id):
	sponsorships = Sponsorship.query.filter_by(issue_id=issue_id).all()
	return sponsorships

def delete_sponsorship(issue_id, user_id):
	sponsorship = retrieve_sponsorship(issue_id, user_id)
	Payment.query.filter_by(sponsorship_id=sponsorship.sponsorship_id).delete()
	db.session.delete(sponsorship)
	db.session.commit()
	

def retrieve_last_payment(sponsorship_id):
	payment = Payment.query.filter_by(sponsorship_id=sponsorship_id) \
			.order_by(Payment.payment_id.desc()).first()
	return payment


def create_change(project_id, method, path, arguments):
	change = Change(project_id, method, path, arguments)
	db.session.add(change)
	db.session.commit()


def notify_sponsors(project_id, issue_id, status, body):
	sponsorships = Sponsorship.query.filter_by(issue_id=issue_id, status=status)
	for sponsorship in sponsorships:
		create_email(project_id, sponsorship.user.user_id, issue_id, body)

def create_email(project_id, user_id, issue_id, body):
	email = Email(project_id, user_id, issue_id, body)
	db.session.add(email)
	db.session.commit()

def send_emails():
	emails = Email.query.all()
	if len(emails) > 0:
		project_ids = set(map(lambda email: email.project_id, emails))
		for project_id in project_ids:
			notify_url = config[project_id].TRACKER_URL + '/bountyfunding/'
			try:
				requests.get(notify_url + 'email', timeout=1)
			except requests.exceptions.RequestException:
				app.logger.warn('Unable to connect to issue tracker at ' + notify_url)


def check_pledge_amount(project_id, amount):
	if amount <= 0:
		raise APIException("Amount must be positive", 400)
	max_pledge_amount = config[project_id].MAX_PLEDGE_AMOUNT
	if amount > max_pledge_amount:
		raise APIException("Amount may be up to %d" % max_pledge_amount, 400)


def notify():
	send_emails()
	t = threading.Timer(NOTIFY_INTERVAL, notify)
	t.daemon = True
	t.start()
