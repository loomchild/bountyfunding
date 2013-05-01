from setuptools import find_packages, setup

setup(
    name='Gang', version='1',
    packages=find_packages(),
    entry_points = {
        'trac.plugins': [
            'gang = gang.gang',
        ],
    },
)
