__test__ = False

import time
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from nose.tools import *
from global_test import create_browser


URL = 'http://localhost:8100'
#URL = 'http://localhost:8200/trac2'
#URL = 'http://demo.bountyfunding.org'
USER = ('user', 'user')
DEV = ('dev', 'dev')

browser = None
ticket_url = None

def setup_module():
	global browser
	browser = create_browser()

def teardown_module():
	global browser
	browser.quit()

def login(who):
	browser.get(URL + '/login')
	user_input = browser.find_element_by_id('user')
	password_input = browser.find_element_by_id('password')
	submit = browser.find_element_by_xpath("//input[@value='Login']")
	user_input.send_keys(who[0])
	password_input.send_keys(who[1])
	submit.click()

def logout():
	browser.get(URL + '/logout')

def get_bountyfunding():
	bf = browser.find_element_by_class_name('bountyfunding')
	return bf


def test_create_and_pledge():
	login(USER)
	
	browser.get(URL + '/newticket')
	summary = browser.find_element_by_id('field-summary')
	summary.send_keys('Test Ticket')
	submit = browser.find_element_by_name('submit')
	submit.click()

	# Store ticket URL
	global ticket_url
	ticket_url = browser.current_url

	browser.get(ticket_url)
	bf = get_bountyfunding()
	amount = bf.find_element_by_name('amount')
	pledge = browser.find_element_by_xpath("//input[@value='Pledge']")
	amount.clear()
	amount.send_keys("10")
	pledge.click()

	# Check if pledge was succesful
	bf = get_bountyfunding()
	label = bf.find_element_by_tag_name('span')
	label_amount = re.sub(r'[^\d]+$', '', re.sub(r'^[^\d]+', '', label.text))
	eq_(label_amount, "10")

	logout()


def test_assign():
	login(DEV)
	
	browser.get(ticket_url)
	modify_ticket = browser.find_element_by_partial_link_text('Modify Ticket')
	modify_ticket.click()
	action = browser.find_element_by_id('action_reassign')
	action.click()
	submit = browser.find_element_by_name('submit')
	submit.click()

	logout()


def test_confirm():
	login(USER)
	
	browser.get(ticket_url)
	confirm_button = browser.find_element_by_id('confirm-button')
	confirm_button.click()
	bf = get_bountyfunding()
	payment_button = bf.find_element_by_name('PLAIN')
	payment_button.click()
	
	# Fill payment details
	card_number = browser.find_element_by_id('card_number')
	card_number.send_keys("4111111111111111")
	card_date = browser.find_element_by_id('card_date')
	card_date.send_keys("05/50")
	pay_button = browser.find_element_by_name('pay')
	pay_button.click()

	# Check if confirmation was succesful
	bf = get_bountyfunding()
	title = bf.find_element_by_tag_name('span').get_attribute('title')
	m = re.search(r'Confirmed:[^\d]*(\d+)', title)
	title_amount = m.group(1)
	eq_(title_amount, "10")
	
	logout()


def test_resolve():
	login(DEV)
	
	browser.get(ticket_url)
	modify_ticket = browser.find_element_by_partial_link_text('Modify Ticket')
	modify_ticket.click()
	action = browser.find_element_by_id('action_resolve')
	action.click()	
	submit = browser.find_element_by_name('submit')
	submit.click()
	
	logout()


def test_validate():
	login(USER)

	browser.get(ticket_url)
	bf = get_bountyfunding()
	validate_button = bf.find_element_by_name('validate')
	validate_button.click()
	
	# Check if confirmation was succesful
	bf = get_bountyfunding()
	title = bf.find_element_by_tag_name('span').get_attribute('title')
	m = re.search(r'Validated:[^\d]*(\d+)', title)
	title_amount = m.group(1)
	eq_(title_amount, "10")
	
	logout()

