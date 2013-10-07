__test__ = False

import time
from selenium import webdriver

browser = None

def setup():
	global browser
	browser = webdriver.Firefox()
	browser.implicitly_wait(3)

def teardown():
	global browser
	browser.quit()

def test_trac_plugin_registered():
	# Access a ticket in trac
	browser.get('http://localhost:8100/ticket/1')
	
	# Check if it contains BountyFunding field
	header = browser.find_element_by_id('h_bountyfunding')
	assert header.text.find('Bounty') == 0, "Header text does not start with Bounty"
