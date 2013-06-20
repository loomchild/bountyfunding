from flask.ext.sqlalchemy import SQLAlchemy
from gang_api import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)

class Issue(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer)
	issue_id = db.Column(db.String(256))
	amount = db.Column(db.Integer)

	def __init__(self, project_id, issue_id):
		self.project_id = project_id
		self.issue_id = issue_id
		self.amount = 0

	def __repr__(self):
		return '<Issue Project ID: "%s", Issue ID: "%s">' % self.project_id, self.issue_id

#class User(db.Model):
#	pass

#class Sponsorship(db.Model):
#	amount = db.Column(db.Integer)

