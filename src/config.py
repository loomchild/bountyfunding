import sys
import os
import re
import ConfigParser
import argparse
import subprocess
from homer import BOUNTYFUNDING_HOME


VERSION = 'Unknown'

TRACKER_URL = ''

DATABASE_URL = ''
DATABASE_IN_MEMORY = False
DATABASE_CREATE = False

PROJECT_DELETE_ALLOW = False


class ConfigurationException:
	def __init__(self, message):
		self.message = message

def init(args):
	config_file = args.config_file
	if not os.path.isabs(config_file):
		config_file = os.path.abspath(os.path.join(BOUNTYFUNDING_HOME, config_file))

	# Read file
	parser = ConfigParser.RawConfigParser()
	parser.readfp(open(config_file))
	
	init_version()

	global TRACKER_URL
	TRACKER_URL = get(parser, 'general', 'tracker_url', TRACKER_URL).strip()

	database_url = get(parser, 'general', 'database_url', DATABASE_URL, args.db_in_memory).strip()
	init_database(database_url)

	global PROJECT_DELETE_ALLOW
	PROJECT_DELETE_ALLOW = get(parser, 'general', 'project_delete_allow', PROJECT_DELETE_ALLOW, args.project_delete_allow, type=bool)


def init_version():
	global VERSION
	try:
		description = subprocess.check_output(["git", "describe", "--long"], 
				stderr=subprocess.STDOUT)
		m = re.match(r"v([\w\.]+)-\d+-g(\w+)", description)
		if m:
			VERSION = m.group(1) + "-" + m.group(2)
	except subprocess.CalledProcessError:
		pass 


def init_database(database_url):
	global DATABASE_URL, DATABASE_IN_MEMORY, DATABASE_CREATE

	DATABASE_URL = database_url

	if DATABASE_URL == 'sqlite://':
		DATABASE_IN_MEMORY = True
		DATABASE_CREATE = True

	elif DATABASE_URL.startswith('sqlite:///'):
		path = database_url[10:]
		
		# Relative path for sqlite database should be based on home directory
		if not os.path.isabs(path):
			path = os.path.join(BOUNTYFUNDING_HOME, path)
			DATABASE_URL = 'sqlite:///' + path

		if not os.path.exists(path):
			DATABASE_CREATE = True

		
def get(parser, section, option, default, override=None, type=str):
	if override:
		return override
	elif parser.has_option(section, option):
		if type == bool:
			value = parser.getboolean(section, option)
		elif type == int:
			value = parser.getint(section, option)
		elif type == float:
			value = parser.getfloat(section, option)
		elif type == str:
			value = parser.get(section, option)
		else:
			raise ConfigurationException("Unknown type: %s" % type)
		return value
	else:
		return default
