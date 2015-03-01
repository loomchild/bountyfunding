#!/usr/bin/env python

from os import path
from argparse import ArgumentParser
from waitress import serve

from bountyfunding import app
from bountyfunding.util.enum import Enum
from bountyfunding.core.config import config
from bountyfunding.api import models
from bountyfunding.core.models import db


# TODO: merge with functions or use real action classes with docstrings
class Action(Enum):
    RUN = 'run'
    CREATE_DB = 'create-db'
    SHELL = 'shell'

def run():
    serve(app, host=config.HOST, port=config.PORT, threads=config.THREADS)

def create_db():
    print 'Creating database in %s' % config.DATABASE_URL
    db.create_all()

def shell():
    namespace = dict(app=app, db=db, config=config, models=models)
  
    with app.app_context():
        # Use IPython if available, otherwise use basic Python shell
        # Trick copied from flask-script
        try:
            from IPython import embed
            embed(user_ns=namespace)
        
        except ImportError:
            import code
            code.interact(local=namespace)


if __name__ == "__main__":
    arg_parser = ArgumentParser(description='BountyFunding')
    
    arg_parser.add_argument('action', 
            action='store', default=Action.RUN, choices=Action.values(),
            nargs='?',
            help='Action to be performed')

    arg_parser.add_argument('-c', '--config-file', 
            action='store', default=None, metavar='FILE',
            help='Specify config file location')

    arg_parser.add_argument('--id', 
            action='store', default='',
            help='Process ID to kill it easier; this parameter is ignored')
    
    arg_parser.add_argument('--host', 
            action='store', default=None, help='Host name / IP address')
    
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
    
    elif action == Action.SHELL:
        shell()

    else: 
        assert False, 'Invalid action: %s' % action 
