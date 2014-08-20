import requests

import urllib

#TODO: move to common module
#import httplib2
#httplib2.debuglevel = 1

from bountyfunding.api.config import config
from bountyfunding.api.models import db, Payment
from bountyfunding.api.const import PaymentGateway


def get_paypal_url(project_id):
	if config[project_id].PAYPAL_SANDBOX:
		paypal_url = 'https://www.sandbox.paypal.com'
	else: 
		paypal_url = 'https://www.paypal.com'
	paypal_url += '/cgi-bin/webscr'
	return paypal_url


def create_payment(project_id, sponsorship, return_url):
	"""
	Returns authorization URL
	"""
	args = {
		"cmd": "_donations",
		"business": config[project_id].PAYPAL_RECEIVER_EMAIL,
		"item_name": "Bounty",
		"amount": sponsorship.amount,
		"currency_code": "EUR",
		"no_note": 1,
		"no_shipping": 1,
		"return": return_url,
		"cancel_return": return_url
	}
	redirect_url = get_paypal_url(project_id) + "?" + urllib.urlencode(args)

	payment = Payment(sponsorship.project_id, sponsorship.sponsorship_id, PaymentGateway.PAYPAL_STANDARD)
	payment.url = redirect_url
	return payment


def process_payment(project_id, sponsorship, payment, details):
	"""
	Validates payment
	"""
	transaction_id = details["tx"]

	payload = {
		"cmd": "_notify-synch",
		"at": config[project_id].PAYPAL_PDT_ACCESS_TOKEN,
		"tx": transaction_id
	}

	# Check for reused transaction ID
	if db.session.query(db.exists().where(Payment.gateway_id==transaction_id)).scalar():
		return False

	r = requests.post(get_paypal_url(project_id), data=payload)
	
	lines = r.text.strip().splitlines()
	
	if len(lines) == 0:
		return False

	# Check for SUCCESS word
	if not lines.pop(0).strip() == "SUCCESS":
		return False

	# Payment validation
	retrieved_payment = {}			
	for line in lines:
		key, value = line.strip().split('=')
		retrieved_payment[key] = urllib.unquote_plus(value)

	# Check recipient email
	if retrieved_payment['business'] != config[project_id].PAYPAL_RECEIVER_EMAIL:
		return False

	# Check currency
	if retrieved_payment['mc_currency'] != "EUR":
		return False

	# Check amount
	if float(retrieved_payment['mc_gross']) != sponsorship.amount:
		return False

	# Store transaction ID
	payment.gateway_id = transaction_id

	return True


