#!/usr/bin/env python

from os import path
from argparse import ArgumentParser

from bountyfunding.util.enum import Enum
from bountyfunding.api.config import config
from bountyfunding.api import app
from bountyfunding.api.models import db


class Action(Enum):
	RUN = 'run'
	CREATE_DB = 'create-db'

def init_db():
	app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
	db.init_app(app)
	# See http://piotr.banaszkiewicz.org/blog/2012/06/29/flask-sqlalchemy-init_app/, option 2
	db.app = app

def run():
	init_db()
	app.run(port=config.PORT, debug=config.DEBUG)

def create_db():
	print 'Creating dabase in %s' % config.DATABASE_URL
	init_db()
	db.create_all()


if __name__ == "__main__":
	arg_parser = ArgumentParser(description='BountyFunding API')
	
	arg_parser.add_argument('action', 
			action='store', default=Action.RUN, choices=Action.values(),
			nargs='?',
			help='Action to be performed')

	arg_parser.add_argument('-c', '--config-file', 
			action='store', 
			default=path.join('conf', 'bountyfunding.ini'),
			metavar='FILE',
			help='Specify config file location (default %(default)s)')

	arg_parser.add_argument('--id', 
			action='store', default='',
			help='Process ID to kill it easier; this parameter is ignored')
	
	arg_parser.add_argument('--port', 
			action='store', type=int, default=None,
			help='Port number')
	
	arg_parser.add_argument('--debug', 
			action='store_true', default=None,
			help='Enable debug mode (use only for testing)')
	
	arg_parser.add_argument('--db-in-memory', 
			action='store_true', default=None,
			help='Use empty in-memory database')

	args = arg_parser.parse_args()
	
	config.init(args)

	if args.action == Action.RUN:
		run()

	elif args.action == Action.CREATE_DB:
		create_db()
	
	else: 
		assert False, 'Invalid action: %s' % args.action 
