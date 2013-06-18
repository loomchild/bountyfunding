#!/usr/bin/env python

from flask import Flask, url_for, render_template, make_response, redirect, abort

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

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

if __name__ == "__main__":
    app.run(debug = True)
