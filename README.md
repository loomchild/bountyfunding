# BountyFunding - Open-Source Bounty Funding Platform
===================================
Website (with live demo): [https://bountyfunding.com](https://bountyfunding.com) 
Development website: [http://bountyfunding.org](http://bountyfunding.org)

Introduction
------------
BountyFunding is a bounty funding platform designed specifically for Free / Open-Source Software. It allows users to collectively sponsor most wanted features / bugfixes, and gives developers another source of income. 

BountyFunding does not duplicate issue tracker functionality, but integrates with an existing solutions. This page describes only core webapp, list of available issue tracker plugins together with their documentation can be found in [Plugins](#plugins). It's possible to connect a plugin to an existing shared BountyHunding platform without deploying it yourself - see http://bountyfunding.com for details.
 
Requirements
------------
* Python (2.7)
* Database (SQLite, MySQL, PostgreSQL - anything supported by SQLAlchemy)
* Message Transfer Agent, such as Postfix or Exim
* Recommended: pip and virtualenv
* Python packages listed in requirements.txt file

Installation
------------

### Download BountyFunding
Download the archive from github [master.zip](https://github.com/bountyfunding/bountyfunding/archive/master.zip) or clone the repository:
	
	git clone https://github.com/bountyfunding/bountyfunding.git

### Install Python Libraries
Run below command to install python dependencies if needed. I use [pip](http://www.pip-installer.org), but they could also be installed with easy_install, packaging system native to your operating system or directly from source. You may consider using [virtualenv](http://www.virtualenv.org) to isolate the installation from other Python applications.

* Install requirements

		pip install -r requirements.txt

### Run BountyFunding webapp

* Configure the BountyFunding webapp. Example configuration file can be found in bountyfunding/conf/bountyfunding.ini.sample, for a simple installation it is enough to duplicate this file and remove the .sample extension, but it's a good idea to look inside to examine available options. You will probably need to change tracker URL and admin user. If you want to use PayPal you'll need to replace project sandbox API credentials with your real ones. 

		cp conf/bountyfunding.ini.sample conf/bountyfunding.ini

* Populate the database. If you are using sqlite database backend (default) then database will be automatically created and populated on the first run. Otherwise you'll need to execute following command:

		./bountyfunding.py create-db

* Run the BountyFunding webapp

		./bountyfunding.py >& log/bountyfunding.log &

* Although BountyFunding embeds production-quality WSGI server (Waitress), it's possible to run it using another one. To do that use bountyfunding.wsgi file located in the main project directory.

Development
-----------
For development you will need all python packages listed in [requirements-dev.txt](requirements-dev.txt):
	
		pip install -r requirements-dev.txt

Plugins
-------
* [Trac](plugin/trac/README.md) 
