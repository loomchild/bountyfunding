#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='BountyFunding', version='0.6',
    packages=find_packages(),
    entry_points = {
        'trac.plugins': [
            'bountyfunding = bountyfunding.bountyfunding',
        ],
    },
	package_data={'bountyfunding': ['templates/*', 'htdocs/styles/*', 'htdocs/scripts/*']},
)
