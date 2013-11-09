#!/usr/bin/env python

from os import path
import argparse
import config
from enum import Enum


class Action(Enum):
	RUN = 'run'
	CREATE_DB = 'create-db'


def run():
	from bountyfunding_api import app
	app.run(port=config.PORT, debug=config.DEBUG)

def create_db():
	from bountyfunding_api.models import db
	print 'Creating dabase in %s' % config.DATABASE_URL
	db.create_all()


if __name__ == "__main__":
	arg_parser = argparse.ArgumentParser(description='BountyFunding API')
	
	arg_parser.add_argument('action', 
			action='store', default=Action.RUN, choices=Action.values(),
			nargs='?',
			help='Action to be performed')

	arg_parser.add_argument('-c', '--config-file', 
			action='store', 
			default=path.join('conf', 'bountyfunding_api.ini'),
			metavar='FILE',
			help='Specify config file location (default %(default)s)')

	arg_parser.add_argument('--port', 
			action='store', type=int, default=None,
			help='Port number')
	
	arg_parser.add_argument('--debug', 
			action='store_true', default=False,
			help='Enable debug mode (use only for testing)')
	
	arg_parser.add_argument('--db-in-memory', 
			action='store_const', const='sqlite://',
			help='Use empty in-memory database')

	arg_parser.add_argument('--project-delete-allow', 
			action='store_true', default=False,
			help='Allow delete project operation (use only for testing)')

	args = arg_parser.parse_args()
	
	config.init(args)

	if args.action == Action.RUN:
		run()

	elif args.action == Action.CREATE_DB:
		create_db()
	
	else: 
		assert False, 'Invalid action: %s' % args.action 
