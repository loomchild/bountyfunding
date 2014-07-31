__test__ = False

from global_test import create_browser
import time

browser = None

def setup():
	global browser
	browser = create_browser()

def teardown():
	global browser
	browser.quit()

def test_trac_plugin_registered():
	# Access a ticket in trac
	browser.get('http://localhost:8100/ticket/1')
	
	# Check if it contains BountyFunding field
	header = browser.find_element_by_id('h_bounty')
	assert header.text.find('Bounty') == 0, "Header text does not start with Bounty"
