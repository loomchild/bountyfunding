import sys
import os
import re
import ConfigParser
import argparse
import subprocess

from bountyfunding.util.homer import BOUNTYFUNDING_HOME
from bountyfunding.api import app
from bountyfunding.api.const import PaymentGateway

from bountyfunding.api.models import db, Config


def parse(name, value):
	p = properties[name]
	v = p.parser(value)
	return v

boolean_states = {'0': False, '1': True, 'false': False, 'no': False, 
	'off': False, 'on': True, 'true': True, 'yes': True}

def boolean(value):
	v = value.lower()
	if v not in boolean_states:
		raise ValueError, 'Not a boolean: %s' % v
	return boolean_states[v]
		
def string_list(value):
	return filter(None, [v.strip() for v in value.split(',')])

def payment_gateway_list(value):
	return [PaymentGateway.from_string(s) for s in string_list(value)]


class Property:
	def __init__(self, description, parser, defualt_value, in_args, in_file, in_db):
		self.description = description
		self.parser = parser
		self.default_value = defualt_value
		self.in_args = in_args
		self.in_file = in_file
		self.in_db = in_db

properties = {
	'VERSION' : Property('Software version', str, 'Unknown', False, False, False),
	'PORT' : Property('Port number', int, 5000, True, True, False),
	'DEBUG' : Property('Enable debug mode (use only for testing)', boolean, False, True, True, False),

	'DATABASE_URL' : Property('SQLAlchemy database url', str, '', False, True, False),
	'DATABASE_IN_MEMORY' : Property('Use empty in-memory database', boolean, False, False, False, False),
	'DATABASE_CREATE' : Property('Create database', boolean, False, False, False, False),
	
	'TRACKER_URL' : Property('Externally accessible location of bug tracker', str, '', False, True, True),
	'ADMIN' : Property('Admin user identifier', str, '', False, True, True),
	'MAX_PLEDGE_AMOUNT' : Property('Maximum pledge amount', int, 100, False, True, True),
	'PAYMENT_GATEWAYS' : Property('List of enabled payment gateways', payment_gateway_list, [PaymentGateway.DUMMY], False, True, True),
		
	'PROJECT_DEFAULT' : Property('Enable default project', boolean, True, False, True, False),
	'PROJECT_TEST' : Property('Enable test projects', boolean, True, False, True, False),
	'PROJECT_ROOT' : Property('Enable root projects', boolean, False, False, True, False),

	'PAYPAL_SANDBOX' : Property('Use Paypal sandbox or live system', boolean, True, False, True, True),
	'PAYPAL_RECEIVER_EMAIL' : Property('Email of the entity receiving payments', str, '', False, True, True),
	'PAYPAL_PDT_ACCESS_TOKEN' : Property('Paypal Payment Data Transfer (PDT) access token', str, '', False, True, True),

	'PAYPAL_USER_ID': Property('Paypal user ID for Adaptive Payments', str, '', False, True, True),
	'PAYPAL_PASSWORD': Property('Paypal password for Adaptive Payments', str, '', False, True, True),
	'PAYPAL_SIGNATURE': Property('Paypal signature for Adaptive Payments', str, '', False, True, True),
	'PAYPAL_APPLICATION_ID': Property('Paypal application ID for Adaptive Payments', str, '', False, True, True),
}


class CommonConfig:
	def __init__(self):
		for name, prop in properties.items():
			setattr(self, name, prop.default_value)
		
	def __getitem__(self, project_id):
		return ProjectConfig(project_id)

	def init(self, args):
		config_file = args.get('config_file')
		if not config_file:
			config_file = os.path.join('conf', 'bountyfunding.ini')
		if not os.path.isabs(config_file):
			config_file = os.path.abspath(os.path.join(BOUNTYFUNDING_HOME, config_file))
		parser = ConfigParser.RawConfigParser()
		parser.readfp(open(config_file))
		
		file_props = filter(lambda (k,v): v.in_file, properties.items())
		for name, prop in file_props:
			self._init_value_from_file(parser, name)

		if args.get('db_in_memory'):
			setattr(self, 'DATABASE_URL', 'sqlite://')

		args_props = filter(lambda (k,v): v.in_args, properties.items())
		for name, prop in args_props:
			self._init_value_from_args(args, name.lower(), name)
		
		self._init_version()
		self._init_database()

	def _init_value_from_file(self, parser, name):
		option = name.lower()
		section = 'general'
		for prefix in ('paypal', 'project', ):
			if option.startswith(prefix):
				section = prefix
				option = option[len(prefix)+1:]
				break
		
		if parser.has_option(section, option):
			value = parser.get(section, option)
			value = parse(name, value)
			setattr(self, name, value)

	def _init_value_from_args(self, args, option, name):
		value = args.get(option)
		if value != None:
			setattr(self, name, value)

	def _init_version(self):
		try:
			description = subprocess.check_output(["git", "describe", "--long", "--tags"], 
					stderr=subprocess.STDOUT)
			m = re.match(r"v([\w\.]+)-\d+-g(\w+)", description)
			if m:
				self.VERSION = m.group(1) + "-" + m.group(2)
		except subprocess.CalledProcessError:
			pass 

	def _init_database(self):
		if self.DATABASE_URL == 'sqlite://':
			self.DATABASE_IN_MEMORY = True
			self.DATABASE_CREATE = True

		elif self.DATABASE_URL.startswith('sqlite:///'):
			path = self.DATABASE_URL[10:]
		
			# Relative path for sqlite database should be based on home directory
			if not os.path.isabs(path):
				path = os.path.join(BOUNTYFUNDING_HOME, path)
				self.DATABASE_URL = 'sqlite:///' + path

			if not os.path.exists(path):
				self.DATABASE_CREATE = True

		app.config['SQLALCHEMY_DATABASE_URI'] = self.DATABASE_URL
		db.init_app(app)
		# See http://piotr.banaszkiewicz.org/blog/2012/06/29/flask-sqlalchemy-init_app/, option 2
		db.app = app

	def _init_property(self, name):
		setattr(self, name, properties[name].default_value)


class ProjectConfig:
	def __init__(self, project_id):
		self.project_id = project_id

	def __getattr__(self, name):
		#TODO: add caching
		if properties[name].in_db:
			prop = self._get_property(self.project_id, name.lower())
			if prop != None:
				value = parse(name, prop.value)
				return value
		return getattr(config, name)

	def _get_property(self, project_id, name):
		prop = Config.query.filter_by(project_id=project_id, name=name).first()
		return prop
		

config = CommonConfig()


