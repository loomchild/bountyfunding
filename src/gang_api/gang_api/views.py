from gang_api import app
from flask import Flask, url_for, render_template, make_response, redirect, abort

@app.route("/issue/<id>")
def hello(id):
	amount = int(id) * 100
	return '{"amount":%s}' % amount


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

