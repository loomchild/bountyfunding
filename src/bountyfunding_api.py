#!/usr/bin/env python

import argparse
import config

def run():
	from bountyfunding_api import app
	app.run(debug=True)

if __name__ == "__main__":
	arg_parser = argparse.ArgumentParser(description='BountyFunding API')

	arg_parser.add_argument('--db-in-memory', action='store_true',
			help='Use empty in-memory database')

	args = arg_parser.parse_args()
	
	config.override(args)
	
	run()
