#!/usr/bin/env python

from setuptools import find_packages, setup

setup(
    name='Gang', version='0.1',
    packages=find_packages(),
    entry_points = {
        'trac.plugins': [
            'gang = gang.gang',
        ],
    },
	package_data={'gang': ['templates/*.html', 'htdocs/styles/*.css']},
)
