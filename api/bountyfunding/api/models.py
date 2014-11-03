from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

from bountyfunding.api.const import SponsorshipStatus, PaymentStatus, PaymentGateway


db = SQLAlchemy()


class Project(db.Model):
	project_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(64), nullable=False)
	description = db.Column(db.String(1024), nullable=False)
	type = db.Column(db.Integer, nullable=False)

	def __init__(self, name, description, type):
		self.name = name
		self.description = description
		self.type = type

	def __repr__(self):
		return '<Project project_id: "%s", name: "%s">' % self.project_id, self.name
	
	def is_mutable(self):
		return True

class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	name = db.Column(db.String(256), nullable=False)
	paypal_email = db.Column(db.String(256), nullable=True)

	def __init__(self, project_id, name):
		self.project_id = project_id
		self.name = name
		paypal_email = None

	def __repr__(self):
		return '<User project_id: "%s", name: "%s">' % self.project_id, self.name

class Issue(db.Model):
	issue_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	issue_ref = db.Column(db.String(256), nullable=False)
	status = db.Column(db.Integer, nullable=False)
	title = db.Column(db.String(1024), nullable=False)
	link = db.Column(db.String(1024), nullable=False)
	owner_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=True)

	owner = db.relation(User, lazy="joined")
	
	def __init__(self, project_id, issue_ref, status, title, link, owner_id):
		self.project_id = project_id
		self.issue_ref = issue_ref
		self.status = status
		self.title = title
		self.link = link
		self.owner_id = owner_id

	def __repr__(self):
		return '<Issue project_id: "%s", issue_ref: "%s">' % self.project_id, self.issue_ref

class Sponsorship(db.Model):
	sponsorship_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	issue_id = db.Column(db.Integer, db.ForeignKey(Issue.issue_id), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=False)
	amount = db.Column(db.Integer, nullable=False)
	status = db.Column(db.Integer, nullable=False)

	user = db.relation(User, lazy="joined")
	
	def __init__(self, project_id, issue_id, user_id, amount=0):
		self.project_id = project_id
		self.issue_id = issue_id
		self.user_id = user_id
		self.amount = amount
		self.status = SponsorshipStatus.PLEDGED

	def __repr__(self):
		return '<Sponsorship issue_id: "%s", user_id: "%s">' % (self.issue_id, self.user_id)
	
class Payment(db.Model):
	payment_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	sponsorship_id = db.Column(db.Integer, db.ForeignKey(Sponsorship.sponsorship_id), nullable=False)
	gateway_id = db.Column(db.String)
	url = db.Column(db.String)
	status = db.Column(db.Integer, nullable=False)
	gateway = db.Column(db.Integer)
	timestamp = db.Column(db.DateTime, nullable=False)

	def __init__(self, project_id, sponsorship_id, gateway):
		self.project_id = project_id
		self.sponsorship_id = sponsorship_id
		self.gateway = gateway
		self.gateway_id = ''
		self.url = ''
		self.status = PaymentStatus.INITIATED
		self.timestamp = datetime.now()

	def __repr__(self):
		return '<Payment payment_id: "%s">' % self.payment_id

class Email(db.Model):
	email_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=False)
	issue_id = db.Column(db.Integer, db.ForeignKey(Issue.issue_id), nullable=False)
	body = db.Column(db.String(1024))

	user = db.relation(User, lazy="joined")
	issue = db.relation(Issue, lazy="joined")
	
	def __init__(self, project_id, user_id, issue_id, body):
		self.project_id = project_id
		self.user_id = user_id
		self.issue_id = issue_id
		self.body = body

	def __repr__(self):
		return '<Email project_id: "%s", user_id: "%s", issue_id: "%s">' %\
				(self.project_id, self.user_id, self.issue_id)


class Change(db.Model):
	change_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	timestamp = db.Column(db.DateTime, nullable=False)
	method = db.Column(db.String(10), nullable=False)
	path = db.Column(db.String(256), nullable=False)
	arguments = db.Column(db.Text(), nullable=False)
	status = db.Column(db.Integer, nullable=True)
	response = db.Column(db.String(4096), nullable=True)

	def __init__(self, project_id, method, path, arguments):
		self.project_id = project_id
		self.timestamp = datetime.now()
		self.method = method
		self.path = path
		self.arguments = arguments

	def __repr__(self):
		return '<Change change_id: "%s"' % (self.change_id,)

class Config(db.Model):
	config_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, nullable=False)
	name = db.Column(db.String(64), nullable=False)
	value = db.Column(db.String(256), nullable=False)
	
	def __init__(self, project_id, name, value):
		self.project_id = project_id
		self.name = name
		self.value = value

	def __repr__(self):
		return '<Config %s-%s: "%s">' % (self.project_id, self.name, self.value)

db.Index('idx_config_pid_name', Config.project_id, Config.name, unique=True)


class Token(db.Model):
	token_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer, db.ForeignKey(Project.project_id), nullable=False)
	token = db.Column(db.String(64), nullable=False)
	
	def __init__(self, project_id, token):
		self.project_id = project_id
		self.token = token

	def __repr__(self):
		return '<Token project_id: "%s", token: "%s">' % (self.project_id, self.token)

db.Index('idx_token_token', Token.token, unique=True)

