import sys
import os
import ConfigParser
import argparse
import subprocess
from homer import BOUNTYFUNDING_HOME

# Default values
defaults = dict(
	tracker_url = "",
	database_url = "",
)

TRACKER_URL = ''
DATABASE_URL = ''
DATABASE_IN_MEMORY = False
DATABASE_CREATE = False
VERSION = ''
HASH = ''

def init(args):
	config_file = args.config_file
	if not os.path.isabs(config_file):
		config_file = os.path.abspath(os.path.join(BOUNTYFUNDING_HOME, config_file))

	# Read file
	parser = ConfigParser.RawConfigParser(defaults)
	parser.readfp(open(config_file))
	
	init_version()

	global TRACKER_URL
	TRACKER_URL = get(parser, 'general', 'tracker_url', '').strip()

	database_url = get(parser, 'general', 'database_url', '', args.db_in_memory).strip()
	init_database(database_url)



def init_version():
	global VERSION, HASH
	VERSION = subprocess.check_output(["git", "describe"]).strip()
	HASH = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).strip()

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

		
def get(parser, section, option, default, override=None):
	if override:
		return override
	elif parser.has_option(section, option):
		return parser.get(section, option)
	else:
		return default
