from gang_api import app
from flask import Flask, url_for, render_template, make_response, redirect, abort, jsonify, request
from models import db, Issue

DEFAULT_PROJECT_ID = 1

@app.route("/issue/<id>")
def get_issue(id):
	issue = Issue.query.filter_by(project_id=DEFAULT_PROJECT_ID, issue_id=id).first()
	if issue != None:
		response = jsonify(amount=issue.amount)
	else:
		response = jsonify(error='Issue not found'), 404
	return response

@app.route("/issue/<id>/sponsors", methods=['POST'])
def post_sponsor(id):
	user = request.values.get('user', None)
	amount = int(request.values.get('amount', 0))
	issue = Issue.query.filter_by(project_id=DEFAULT_PROJECT_ID, issue_id=id).first()
	if issue != None:
		issue.amount += amount
		db.session.add(issue)
		db.session.commit()
		response = jsonify(message='Issue updated')
	else:
		response = jsonify(error='Issue not found'), 404
	return response



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

