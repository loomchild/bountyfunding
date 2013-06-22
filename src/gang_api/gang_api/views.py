from gang_api import app
from flask import Flask, url_for, render_template, make_response, redirect, abort, jsonify, request
from models import db, Issue, User, Sponsorship
from pprint import pprint


DEFAULT_PROJECT_ID = 1

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
		result = db.session.query(Sponsorship.issue_id, Sponsorship.amount, User.name)\
				.filter_by(issue_id=issue.issue_id).join(Sponsorship.user).all()
		sponsorships = dict(map(lambda r: (r.name, {'amount': r.amount}), result))
		response = jsonify(sponsorships)
	else:
		response = jsonify(error='Issue not found'), 404
	return response


@app.route("/issue/<issue_ref>/sponsorships", methods=['POST'])
def post_sponsorship(issue_ref):
	user_name = request.values.get('user', None)
	amount = int(request.values.get('amount', 0))
	if amount < 0:
		amount = 0

	issue = retrieve_create_issue(DEFAULT_PROJECT_ID, issue_ref)

	user = User.query.filter_by(project_id=DEFAULT_PROJECT_ID, name=user_name).first()
	if user == None:
		user = User(project_id=DEFAULT_PROJECT_ID, name=user_name)
		db.session.add(user)
		db.session.commit()
	sponsorship = Sponsorship.query.filter_by(issue_id=issue.issue_id, user_id=user.user_id).first()
	if sponsorship == None:
		sponsorship = Sponsorship(issue.issue_id, user.user_id)
	sponsorship.amount = amount
	db.session.add(sponsorship)
	db.session.commit()

	response = jsonify(message='Sponsorship updated')
	return response

@app.route("/issue/<issue_ref>/status", methods=['POST'])
def post_status(issue_ref):
	status = request.values.get('status', None)

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

