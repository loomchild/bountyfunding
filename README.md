Gang - Open-Source Funding Platform
===================================
Website:  gang.loomchild.net

Introduction
------------
What it is

Requirements
------------
Python (2.6)
Flask (0.9)
SqlAlchemy (0.16) 
Database (sqlite, mysql, postgresql, anything supported SQLAlchemy)

Integration
-----------
Currently Gang only intehrates with Trac (1.0). Other issue tracking plugins will be developed soon (they are quite easy to write as most of the business logic resides in the API).

Installation
------------
Install dependencies:
pip Flask
pip ...
Install Trac
[need to add complete package build]

git clone
[need build tool for python, to build the whole thing]

cd plugins/gang_api_plugin/src (it should be gang_api_plugin/src)
drop that egg

cd src/gang_api
./gang_api.py

Troubleshooting
Logs location for Trac

Live Demo
---------
[Demo] (http://demo.gang.loomchild.net)

