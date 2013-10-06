import sys
from os import path
import ConfigParser
import argparse
from homer import BOUNTYFUNDING_HOME

# Default values
defaults = dict(
	tracker_url = "",
	database_url = "",
)

TRACKER_URL = ''
DATABASE_URL = ''
DATABASE_IN_MEMORY = False

def init(args):
	config_file = args.config_file
	if not path.isabs(config_file):
		config_file = path.abspath(path.join(BOUNTYFUNDING_HOME, config_file))

	# Read file
	parser = ConfigParser.RawConfigParser(defaults)
	parser.readfp(open(config_file))

	# Expose values
	global TRACKER_URL, DATABASE_URL, DATABASE_IN_MEMORY
	TRACKER_URL = get(parser, 'general', 'tracker_url', '')
	DATABASE_URL = get(parser, 'general', 'database_url', '', args.db_in_memory)
	DATABASE_IN_MEMORY = (DATABASE_URL == 'sqlite://')

def get(parser, section, option, default, override=None):
	if override:
		return override
	elif parser.has_option(section, option):
		return parser.get(section, option)
	else:
		return default
