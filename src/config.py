import sys
import os
import re
import ConfigParser
import argparse
import subprocess
from homer import BOUNTYFUNDING_HOME
from const import PaymentGateway


class Property:
	def __init__(self, description, typ, defualt_value, section, in_args, in_file, in_db):
		self.description = description
		self.typ = typ
		self.default_value = defualt_value
		self.section = section
		self.in_args = in_args
		self.in_file = in_file
		self.in_db = in_db

properties = {
	'VERSION' : Property('Software version', str, 'Unknown', 'general', False, False, False),
	'PORT' : Property('Port number', int, 5000, 'general', True, True, False),
	'DEBUG' : Property('Enable debug mode (use only for testing)', bool, False, 'general', True, True, False),

	'DATABASE_URL' : Property('SQLAlchemy database url', str, '', 'general', False, True, False),
	'DATABASE_IN_MEMORY' : Property('Use empty in-memory database', bool, False, 'general', False, False, False),
	'DATABASE_CREATE' : Property('Create database', bool, False, 'general', False, False, False),
	
	'TRACKER_URL' : Property('Externally accessible location of bug tracker', str, '', 'project', False, True, True),
	'MAX_PLEDGE_AMOUNT' : Property('Maximum pledge amount', int, 100, 'project', False, True, True),
	'PAYMENT_GATEWAYS' : Property('List of enabled payment gateways', list, [PaymentGateway.PLAIN], 'project', False, True, True),
		
	'PAYPAL_SANDBOX' : Property('Use Paypal sandbox or live system', bool, True, 'paypal', False, True, True),
	'PAYPAL_RECEIVER_EMAIL' : Property('Email of the entity receiving payments; must match with other details like tokens, etc', str, '', 'paypal', False, True, True),
	'PAYPAL_CLIENT_ID' : Property('RESTful API client ID', str, '', 'paypal', False, True, True),
	'PAYPAL_CLIENT_SECRET' : Property('RESTful API client secret', str, '', 'paypal', False, True, True),
	'PAYPAL_PDT_ACCESS_TOKEN' : Property('Paypal Payment Data Transfer (PDT) access token', str, '', 'paypal', False, True, True),
}


def parse(typ, value):
	p = parsers[typ]
	v = p(value)
	return v

boolean_states = {'0': False, '1': True, 'false': False, 'no': False, 
	'off': False, 'on': True, 'true': True, 'yes': True}

def parse_bool(value):
	v = value.lower()
	if v not in boolean_states:
		raise ValueError, 'Not a boolean: %s' % v
	return boolean_states[v]

def parse_str(value):
	return value.strip()

def parse_int(value):
	return int(value)

def parse_float(value):
	return int(value)
		
def parse_list(value):
	return filter(None, [v.strip() for v in value.split(',')])

parsers = {
	str : parse_str,
	bool : parse_bool,
	int : parse_int,
	float : parse_float,
	list : parse_list,
}


class CommonConfig:
	def __init__(self):
		for name, prop in properties.items():
			setattr(self, name, prop.default_value)
		
	def init(self, args):
		config_file = args.config_file
		if not os.path.isabs(config_file):
			config_file = os.path.abspath(os.path.join(BOUNTYFUNDING_HOME, config_file))
		parser = ConfigParser.RawConfigParser()
		parser.readfp(open(config_file))
		
		file_props = filter(lambda (k,v): v.in_file, properties.items())
		for name, prop in file_props:
			self._init_value_from_file(parser, prop.section, name.lower(), name)

		if args.db_in_memory:
			setattr(self, 'DATABASE_URL', 'sqlite://')

		args_props = filter(lambda (k,v): v.in_args, properties.items())
		for name, prop in args_props:
			self._init_value_from_args(args, name.lower(), name)
		
		self._init_version()
		self._init_database()

	def _init_value_from_file(self, parser, section, option, name):
		if parser.has_option(section, option):
			value = parser.get(section, option)
			prop = properties[name]
			value = parse(prop.typ, value)
			setattr(self, name, value)

	def _init_value_from_args(self, args, option, name):
		value = getattr(args, option)
		if value != None:
			setattr(self, name, value)

	def _init_version(self):
		try:
			description = subprocess.check_output(["git", "describe", "--long"], 
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

	def _init_property(self, name):
		setattr(self, name, properties[name].default_value)

class ProjectConfig:
	pass

class ConfigurationException:
	def __init__(self, message):
		self.message = message

config = CommonConfig()
