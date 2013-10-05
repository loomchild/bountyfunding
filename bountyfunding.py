from paver.easy import *
from paver.virtual import virtualenv

options(
    setup=dict(
		name='BountyFunding',
		version="0.2",
		description='Open-Source Bounty Funding Platform',
		author='Jarek Lipski',
		author_email='pub@loomchild.net',
		packages=['bountyfunding_api'],
		install_requires=[],
		#test_suite='nose.collector',
		#entry_points="""
		#[console_scripts]
		#paver = paver.command:main
		#""",
    ),
	virtualenv=dict()
)

@task
@cmdopts([
    ('background', 'b', 'Run in background and log to a file')
])
@virtualenv(dir="virtualenv")
def start(options):
	"""Run BountyFunding API"""

	command = "./bountyfunding_api.py" 
	if hasattr(options, "background"):
		command += " > ../log/bountyfunding_api.log 2>&1 &"
	
	sh(command, cwd="src")

@task
def stop():
	"""Stop BountyFunding API"""
	sh("pkill -f bountyfunding_api", ignore_error = True)
