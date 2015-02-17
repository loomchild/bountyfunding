#!/usr/bin/env python

from os import path
from argparse import ArgumentParser
from waitress import serve

from bountyfunding import app
from bountyfunding.util.enum import Enum
from bountyfunding.api.config import config
from bountyfunding.api.models import db


class Action(Enum):
    RUN = 'run'
    CREATE_DB = 'create-db'

def run():
    serve(app, host='0.0.0.0', port=config.PORT, threads=config.THREADS)

def create_db():
    print 'Creating database in %s' % config.DATABASE_URL
    db.create_all()


if __name__ == "__main__":
    arg_parser = ArgumentParser(description='BountyFunding')
    
    arg_parser.add_argument('action', 
            action='store', default=Action.RUN, choices=Action.values(),
            nargs='?',
            help='Action to be performed')

    arg_parser.add_argument('-c', '--config-file', 
            action='store', default=None,
            metavar='FILE',
            help='Specify config file location')

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

    arg_parser.add_argument('--threads', 
            action='store', type=int, default=None,
            help='Number of worker threads')

    args = vars(arg_parser.parse_args())
   
    config.init(args)

    action = args['action']
    if action == Action.RUN:
        run()

    elif action == Action.CREATE_DB:
        create_db()
    
    else: 
        assert False, 'Invalid action: %s' % args.action 
