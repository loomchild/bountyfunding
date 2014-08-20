#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='BountyFunding', 
	namespace_packages = ['bountyfunding'],
	version='0.6',
    packages=find_packages(),
    entry_points = {
        'trac.plugins': [
            'bountyfunding = bountyfunding.trac.bountyfunding',
        ],
    },
	package_data={'bountyfunding.trac': ['templates/*', 'htdocs/styles/*', 'htdocs/scripts/*']},
)
