#!/usr/bin/env python

from os import path
import argparse
import config

def run():
	from bountyfunding_api import app
	app.run(debug=True)

if __name__ == "__main__":
	arg_parser = argparse.ArgumentParser(description='BountyFunding API')
	
	arg_parser.add_argument('-c', '--config-file', 
			action='store', 
			default=path.join('conf', 'bountyfunding_api.ini'),
			metavar='FILE',
			help='Specify config file location (default %(default)s)')

	arg_parser.add_argument('--db-in-memory', 
			action='store_const', const='sqlite://',
			help='Use empty in-memory database')

	args = arg_parser.parse_args()
	
	config.init(args)
	
	run()
