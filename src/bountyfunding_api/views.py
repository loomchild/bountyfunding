from bountyfunding_api import app
from flask import Flask, url_for, render_template, make_response, redirect, abort, jsonify, request
from models import db, Issue, User, Sponsorship, Email, Payment
from pprint import pprint
import paypal_rest
import config
import re, requests, threading

DEFAULT_PROJECT_ID = 1
DATE_PATTERN = re.compile('^(0?[1-9]|1[012])/[0-9][0-9]$')

NOTIFY_URL = config.TRACKER_URL + '/bountyfunding/'
NOTIFY_INTERVAL = 5


@app.route('/version', methods=['GET'])
def status():
	return jsonify(version=config.VERSION)

@app.route("/issue/<issue_ref>", methods=['GET'])
def get_issue(issue_ref):
	issue = retrieve_issue(DEFAULT_PROJECT_ID, issue_ref)
	if issue != None:
		status = Issue.Status.to_string(issue.status)
		response = jsonify(status=status)
	else:
		response = jsonify(error='Issue not found'), 404
	return response

@app.route("/issue/<issue_ref>/sponsorships", methods=['GET'])
def get_sponsorships(issue_ref):
	sponsorships = []
	issue = retrieve_issue(DEFAULT_PROJECT_ID, issue_ref)

	if issue != None:
		sponsorships = Sponsorship.query.filter_by(issue_id=issue.issue_id).all()
		sponsorships = dict(map(\
				lambda s: (s.user.name, \
				{'amount': s.amount, 'status': Sponsorship.Status.to_string(s.status)}),\
				sponsorships))
		response = jsonify(sponsorships)
	else:
		response = jsonify(error='Issue not found'), 404
	return response


@app.route("/issue/<issue_ref>/sponsorships", methods=['POST'])
def post_sponsorship(issue_ref):
	user_name = request.values.get('user')
	amount = request.values.get('amount')

	issue = retrieve_create_issue(DEFAULT_PROJECT_ID, issue_ref)
	user = retrieve_create_user(DEFAULT_PROJECT_ID, user_name)
	
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
	if sponsorship == None:
		sponsorship = Sponsorship(issue.issue_id, user.user_id)

	if amount != None:
		sponsorship.amount = int(max(amount, 0))
	
	db.session.add(sponsorship)
	db.session.commit()

	response = jsonify(message='Sponsorship updated')
	return response


@app.route("/issue/<issue_ref>/sponsorship/<user_name>/status", methods=['PUT'])
def update_sponsorship(issue_ref, user_name):
	status = Sponsorship.Status.from_string(request.values.get('status')) 

	issue = retrieve_create_issue(DEFAULT_PROJECT_ID, issue_ref)
	user = retrieve_create_user(DEFAULT_PROJECT_ID, user_name)
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)

	if status == Sponsorship.Status.CONFIRMED:
		response = jsonify(error='Confirm sponsorship by confirming the payment'), 400

	sponsorship.status = status
	
	db.session.add(sponsorship)
	db.session.commit()

	response = jsonify(message='Sponsorship updated')
	return response

@app.route("/issue/<issue_ref>/sponsorship/<user_name>/payment", methods=['GET'])
def get_payment(issue_ref, user_name):
	issue = retrieve_issue(DEFAULT_PROJECT_ID, issue_ref)
	user = retrieve_user(DEFAULT_PROJECT_ID, user_name)
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)

	payment = retrieve_last_payment(sponsorship.sponsorship_id)

	if payment != None:
		gateway = Payment.Gateway.to_string(payment.gateway)
		status = Payment.Status.to_string(payment.status)
		response = jsonify(gateway=gateway, url=payment.url, status=status)
	else:
		response = jsonify(error='Payment not found'), 404
	
	return response

@app.route("/issue/<issue_ref>/sponsorship/<user_name>/payment", methods=['PUT'])
def update_payment(issue_ref, user_name):
	status = Payment.Status.from_string(request.values.get('status')) 
	if status != Payment.Status.CONFIRMED:
		return jsonify(error='You can only change the status to CONFIRMED')
	
	issue = retrieve_issue(DEFAULT_PROJECT_ID, issue_ref)
	user = retrieve_user(DEFAULT_PROJECT_ID, user_name)
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)

	payment = retrieve_last_payment(sponsorship.sponsorship_id)

	if payment != None:
		if payment.status == status:
			return jsonify(error='Payment already confirmed'), 400
		if payment.gateway == Payment.Gateway.PLAIN:
			card_number = request.values.get('card_number')
			card_date = request.values.get('card_date')
			if card_number != '4111111111111111' or DATE_PATTERN.match(card_date) == None:
				return jsonify(error='Invalid card details'), 400
		elif payment.gateway == Payment.Gateway.PAYPAL:
			payer_id = request.values.get('payer_id')
			approved = paypal_rest.execute_payment(payment.gateway_id, payer_id)
			if not approved:
				return jsonify(error='Payment not confirmed by PayPal'), 400
		else:
			return jsonify(error='Unknown gateway'), 400

		payment.status = status
		db.session.add(payment)
		sponsorship.status = Sponsorship.Status.CONFIRMED
		db.session.add(sponsorship)
		db.session.commit()
		response = jsonify(message='Payment updated')
	else:
		response = jsonify(error='Payment not found'), 404
	
	return response

@app.route("/issue/<issue_ref>/sponsorship/<user_name>/payments", methods=['POST'])
def create_payment(issue_ref, user_name):
	gateway = Payment.Gateway.from_string(request.values.get('gateway')) 
	return_url = request.values.get('return_url')
	
	issue = retrieve_issue(DEFAULT_PROJECT_ID, issue_ref)
	user = retrieve_user(DEFAULT_PROJECT_ID, user_name)
	sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
	
	payment = Payment(sponsorship.sponsorship_id, gateway)

	if gateway == Payment.Gateway.PLAIN:
		pass
	elif gateway == Payment.Gateway.PAYPAL:
		if not return_url:
			return jsonify(error='return_url cannot be blank'), 400
		payment.gateway_id, payment.url = paypal_rest.create_payment(sponsorship.amount, return_url)
	else:
		return jsonify(error='Unknown gateway'), 400
	payment.gateway = gateway

	db.session.add(payment)
	db.session.commit()
	
	response = jsonify(message='Payment created')
	return response

@app.route("/issue/<issue_ref>/status", methods=['PUT'])
def update_status(issue_ref):
	status = Issue.Status.from_string(request.values.get('status'))

	issue = retrieve_create_issue(DEFAULT_PROJECT_ID, issue_ref)
	
	issue.status = status
	db.session.add(issue)
	db.session.commit()

	if issue.status == Issue.Status.ASSIGNED:
		subject = 'Task assigned %s' % issue.issue_ref
		body = 'The task you have sponsored has been accepted by the developer. Please deposit the promised amount. To do that please go to project issue tracker at %s, log in, find an issue ID %s and select Confirm.' % (config.TRACKER_URL, issue.issue_ref)
		notify_sponsors(issue.issue_id, Sponsorship.Status.PLEDGED, subject, body)

		sponsorships = Sponsorship.query.filter_by(issue_id=issue.issue_id, status=Sponsorship.Status.PLEDGED)
	elif issue.status == Issue.Status.COMPLETED:
		subject = 'Task completed %s' % issue.issue_ref
		
		body_confirmed = 'The task you have sponsored has been completed by the developer. Please verify it. To do that please go to project issue tracker at %s, log in, find an issue ID %s and select Validate.' % (config.TRACKER_URL, issue.issue_ref)
		notify_sponsors(issue.issue_id, Sponsorship.Status.CONFIRMED, subject, body_confirmed)
		
		body_pledged = 'The task you have sponsored has been completed by the developer. Please deposit the promised amout and verify it. To do that please go to project issue tracker at %s, log in, find an issue ID %s and select Confirm and then Validate.' % (config.TRACKER_URL, issue.issue_ref)
		notify_sponsors(issue.issue_id, Sponsorship.Status.PLEDGED, subject, body_pledged)

	response = jsonify(message='Issue updated')
	return response


@app.route('/emails', methods=['GET'])
def get_emails():
	emails = Email.query.all()

	response = []
	for email in emails:
		response.append({'id': email.email_id, 'recipient':email.user.name, 'subject':email.subject, 'body':email.body})
		
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


def retrieve_issue(project_id, issue_ref):
	issue = Issue.query.filter_by(project_id=DEFAULT_PROJECT_ID, issue_ref=issue_ref).first()
	return issue

def retrieve_create_issue(project_id, issue_ref):
	issue = retrieve_issue(project_id, issue_ref)
	if issue == None:
		issue = Issue(project_id=DEFAULT_PROJECT_ID, issue_ref=issue_ref)
		db.session.add(issue)
		db.session.commit()
	return issue

def retrieve_user(project_id, name):
	user = User.query.filter_by(project_id=DEFAULT_PROJECT_ID, name=name).first()
	return user

def retrieve_create_user(project_id, name):
	user = retrieve_user(project_id, name)
	if user == None:
		user = User(project_id=DEFAULT_PROJECT_ID, name=name)
		db.session.add(user)
		db.session.commit()
	return user

def retrieve_sponsorship(issue_id, user_id):
	sponsorship = Sponsorship.query.filter_by(issue_id=issue_id, user_id=user_id).first()
	return sponsorship

def retrieve_last_payment(sponsorship_id):
	payment = Payment.query.filter_by(sponsorship_id=sponsorship_id) \
			.order_by(Payment.payment_id.desc()).first()
	return payment


def notify_sponsors(issue_id, status, subject, body):
	sponsorships = Sponsorship.query.filter_by(issue_id=issue_id, status=status)
	for sponsorship in sponsorships:
		create_email(sponsorship.user.user_id, subject, body)

def create_email(user_id, subject, body):
	email = Email(DEFAULT_PROJECT_ID, user_id, subject, body)
	db.session.add(email)
	db.session.commit()

def send_emails():
	if db.session.query(db.exists().where(Email.project_id==DEFAULT_PROJECT_ID)).scalar():
		try:
			requests.get(NOTIFY_URL + 'email', timeout=1)
		except requests.exceptions.RequestException:
			app.logger.warn('Unable to connect to issue tracker at ' + NOTIFY_URL)

def notify():
	send_emails()
	t = threading.Timer(NOTIFY_INTERVAL, notify)
	t.daemon = True
	t.start()

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
	

# Examples
#@app.route('/user/static')
#def show_static_user():
#	response = make_response(url_for('static', filename='test.txt'))
#	return response
#
#@app.route('/director')
#def redirector():
#	return redirect(url_for('show_user_profile', username='Director'))
#
#@app.route('/error')
#def error():
#	app.logger.error('An error occurred')
#	abort(401)

