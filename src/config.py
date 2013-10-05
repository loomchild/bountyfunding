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


# Expose values
TRACKER_URL = cfg_parser.get('general', 'tracker_url')
DATABASE_URL = cfg_parser.get('general', 'database_url')
DATABASE_IN_MEMORY = (DATABASE_URL == 'sqlite://')


# Override values by command-line arguments
def override(args):
	global DATABASE_URL
	global DATABASE_IN_MEMORY
		
	if args.db_in_memory:
		DATABASE_IN_MEMORY = True
		DATABASE_URL = 'sqlite://'


