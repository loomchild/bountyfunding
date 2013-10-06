__test__ = False

import time
from selenium import webdriver

browser = None

def setup():
	global browser
	browser = webdriver.Firefox()

def teardown():
	global browser
	browser.quit()

def test():
	browser.get('http://localhost:8100')
	time.sleep(10)
