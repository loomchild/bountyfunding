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


# Read file
CONFIG_FILE = path.abspath(path.join(BOUNTYFUNDING_HOME, 'conf', 'bountyfunding_api.ini'))
cfg_parser = ConfigParser.RawConfigParser(defaults)
cfg_parser.readfp(open(CONFIG_FILE))


# Override values by command-line arguments
arg_parser = argparse.ArgumentParser(description='BountyFunding API')

arg_parser.add_argument('--db-in-memory', action='store_true',
		help='Use empty in-memory database')

args = arg_parser.parse_args()

if args.db_in_memory:
	cfg_parser.set('general', 'database_url', 'sqlite://')


# Expose values
TRACKER_URL = cfg_parser.get('general', 'tracker_url')
DATABASE_URL = cfg_parser.get('general', 'database_url')
DATABASE_IN_MEMORY = (DATABASE_URL == 'sqlite://')
