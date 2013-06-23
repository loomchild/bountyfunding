from gang_api import app
from flask import Flask, url_for, render_template, make_response, redirect, abort, jsonify, request
from models import db, Issue, User, Sponsorship
from pprint import pprint
import re

DEFAULT_PROJECT_ID = 1
DATE_PATTERN = re.compile('^(0?[1-9]|1[012])/[0-9][0-9]$')

@app.route("/issue/<issue_ref>")
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
		result = db.session.query(Sponsorship.issue_id, Sponsorship.amount, Sponsorship.status, User.name)\
				.filter_by(issue_id=issue.issue_id).join(Sponsorship.user).all()
		sponsorships = dict(map(\
				lambda r: (r.name, {'amount': r.amount, 'status': Sponsorship.Status.to_string(r.status)}),\
				result))
		response = jsonify(sponsorships)
	else:
		response = jsonify(error='Issue not found'), 404
	return response


@app.route("/issue/<issue_ref>/sponsorships", methods=['POST'])
def post_sponsorship(issue_ref):
	user_name = request.values.get('user')
	amount = request.values.get('amount')

	issue = retrieve_create_issue(DEFAULT_PROJECT_ID, issue_ref)

	user = User.query.filter_by(project_id=DEFAULT_PROJECT_ID, name=user_name).first()
	if user == None:
		user = User(project_id=DEFAULT_PROJECT_ID, name=user_name)
		db.session.add(user)
		db.session.commit()
	sponsorship = Sponsorship.query.filter_by(issue_id=issue.issue_id, user_id=user.user_id).first()
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
	status_string = request.values.get('status')
	status = Sponsorship.Status.from_string(status_string) if status_string != None else None 

	issue = retrieve_create_issue(DEFAULT_PROJECT_ID, issue_ref)

	user = User.query.filter_by(project_id=DEFAULT_PROJECT_ID, name=user_name).first()
	if user == None:
		user = User(project_id=DEFAULT_PROJECT_ID, name=user_name)
		db.session.add(user)
		db.session.commit()

	sponsorship = Sponsorship.query.filter_by(issue_id=issue.issue_id, user_id=user.user_id).first()

	if status == Sponsorship.Status.CONFIRMED:
		card_number = request.values.get('card_number')
		card_date = request.values.get('card_date')
		if card_number != '4111111111111111' or DATE_PATTERN.match(card_date) == None:
			return jsonify(error='Invalid card details'), 400

	sponsorship.status = status
	
	db.session.add(sponsorship)
	db.session.commit()

	response = jsonify(message='Sponsorship updated')
	return response


@app.route("/issue/<issue_ref>/status", methods=['PUT'])
def post_status(issue_ref):
	status = request.values.get('status')

	issue = retrieve_create_issue(DEFAULT_PROJECT_ID, issue_ref)
	
	issue.status = Issue.Status.from_string(status)
	db.session.add(issue)
	db.session.commit()

	response = jsonify(message='Sponsorship updated')
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



# Examples
@app.route('/user/<username>')
def show_user_profile(username):
	return 'User %s' % username

@app.route('/user/<username>', methods=['POST'])
def create_user_profile(username):
	return 'Created %s' % username

@app.route('/user/static')
def show_static_user():
	response = make_response(url_for('static', filename='test.txt'))
	return response

@app.route('/templar/')
@app.route('/templar/<name>')
def templar(name=None):
	return render_template('hello.html', name=name)

@app.route('/director')
def redirector():
	return redirect(url_for('show_user_profile', username='Director'))

@app.route('/error')
def error():
	app.logger.error('An error occurred')
	abort(401)

