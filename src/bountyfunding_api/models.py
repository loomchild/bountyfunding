
from flask.ext.sqlalchemy import SQLAlchemy
from enum import Enum 
from bountyfunding_api import app
import config
from const import SponsorshipStatus, PaymentStatus, PaymentGateway
#import logging


app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
db = SQLAlchemy(app)


#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class Issue(db.Model):
	issue_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	issue_ref = db.Column(db.String(256), nullable=False)

	def __init__(self, project_id, issue_ref):
		self.project_id = project_id
		self.issue_ref = issue_ref

	def __repr__(self):
		return '<Issue project_id: "%s", issue_ref: "%s">' % self.project_id, self.issue_ref

class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	name = db.Column(db.String(256), nullable=False)

	def __init__(self, project_id, name):
		self.project_id = project_id
		self.name = name

	def __repr__(self):
		return '<User project_id: "%s", name: "%s">' % self.project_id, self.name

class Sponsorship(db.Model):
	sponsorship_id = db.Column(db.Integer, primary_key=True)
	issue_id = db.Column(db.Integer, db.ForeignKey(Issue.issue_id), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=False)
	amount = db.Column(db.Integer, nullable=False)
	status = db.Column(db.Integer, nullable=False)

	user = db.relation(User, lazy="joined")
	
	def __init__(self, issue_id, user_id, amount=0):
		self.issue_id = issue_id
		self.user_id = user_id
		self.amount = amount
		self.status = SponsorshipStatus.PLEDGED

	def __repr__(self):
		return '<Sponsorship issue_id: "%s", user_id: "%s">' % (self.issue_id, self.user_id)
	
class Payment(db.Model):
	payment_id = db.Column(db.Integer, primary_key=True)
	sponsorship_id = db.Column(db.Integer, db.ForeignKey(Sponsorship.sponsorship_id), nullable=False)
	gateway_id = db.Column(db.String)
	url = db.Column(db.String)
	status = db.Column(db.Integer, nullable=False)
	gateway = db.Column(db.Integer)

	def __init__(self, sponsorship_id, gateway):
		self.sponsorship_id = sponsorship_id
		self.gateway = gateway
		self.gateway_id = ''
		self.url = ''
		self.status = PaymentStatus.INITIATED

	def __repr__(self):
		return '<Payment payment_id: "%s">' % self.payment_id

class Email(db.Model):
	email_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=False)
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

