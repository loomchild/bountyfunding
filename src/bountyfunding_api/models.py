
from flask.ext.sqlalchemy import SQLAlchemy
from utils import Enum 
from os import path
import os
import re
from bountyfunding_api import app
from homer import BOUNTYFUNDING_HOME
import config
#import logging

database_url = config.DATABASE_URL

# Relative path for sqlite database should be based on home directory
database_url = re.sub("(?<=sqlite://)/(?!/)", 
		"/" + path.join(BOUNTYFUNDING_HOME, ""), database_url)

# TODO: log
print("Database: " + database_url)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
db = SQLAlchemy(app)


#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class Issue(db.Model):
	issue_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer)
	issue_ref = db.Column(db.String(256))
	status = db.Column(db.Integer)

	class Status(Enum):
		NEW = 10
		ASSIGNED = 20
		COMPLETED = 30
		DELETED = 90

	def __init__(self, project_id, issue_ref):
		self.project_id = project_id
		self.issue_ref = issue_ref
		self.status = Issue.Status.NEW

	def __repr__(self):
		return '<Issue project_id: "%s", issue_ref: "%s">' % self.project_id, self.issue_ref

class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer)
	name = db.Column(db.String(256))

	def __init__(self, project_id, name):
		self.project_id = project_id
		self.name = name

	def __repr__(self):
		return '<User project_id: "%s", name: "%s">' % self.project_id, self.name

class Sponsorship(db.Model):
	sponsorship_id = db.Column(db.Integer, primary_key=True)
	issue_id = db.Column(db.Integer, db.ForeignKey(Issue.issue_id))
	user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
	amount = db.Column(db.Integer)
	status = db.Column(db.Integer)

	user = db.relation(User, lazy="joined")
	
	class Status(Enum):
		PLEDGED = 10
		CONFIRMED = 20
		VALIDATED = 30

	def __init__(self, issue_id, user_id, amount=0):
		self.issue_id = issue_id
		self.user_id = user_id
		self.amount = amount
		self.status = Sponsorship.Status.PLEDGED

	def __repr__(self):
		return '<Sponsorship issue_id: "%s", user_id: "%s">' % (self.issue_id, self.user_id)
	
class Payment(db.Model):
	payment_id = db.Column(db.Integer, primary_key=True)
	sponsorship_id = db.Column(db.Integer, db.ForeignKey(Sponsorship.sponsorship_id))
	gateway_id = db.Column(db.String)
	url = db.Column(db.String)
	status = db.Column(db.Integer)
	gateway = db.Column(db.Integer)

	class Status(Enum):
		INITIATED = 10
		CONFIRMED = 20

	class Gateway(Enum):
		PLAIN = 10
		PAYPAL = 20

	def __init__(self, sponsorship_id, gateway):
		self.sponsorship_id = sponsorship_id
		self.gateway = gateway
		self.gateway_id = ''
		self.url = ''
		self.status = Payment.Status.INITIATED

	def __repr__(self):
		return '<Payment payment_id: "%s">' % self.payment_id

class Email(db.Model):
	email_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer)
	user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
	subject = db.Column(db.String(128))
	body = db.Column(db.String(1024))

	user = db.relation(User, lazy="joined")
	
	def __init__(self, project_id, user_id, subject, body):
		self.project_id = project_id
		self.user_id = user_id
		self.subject = subject
		self.body = body

	def __repr__(self):
		return '<Email project_id: "%s", user_id: "%s", subject: "%s">' %\
				(self.project_id, self.user_id, self.subject)

