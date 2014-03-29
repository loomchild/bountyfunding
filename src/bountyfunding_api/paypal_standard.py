import requests

import urllib

import httplib2
httplib2.debuglevel = 1

from config import config
from models import db, Payment
from const import PaymentGateway

if config.PAYPAL_SANDBOX:
	PAYPAL_URL = 'https://www.sandbox.paypal.com'
else: 
	PAYPAL_URL = 'https://www.paypal.com'
PAYPAL_URL += '/cgi-bin/webscr'


def create_payment(sponsorship, return_url):
	"""
	Returns authorization URL
	"""
	args = {
		"cmd": "_donations",
		"business": config.PAYPAL_RECEIVER_EMAIL,
		"item_name": "Bounty",
		"amount": sponsorship.amount,
		"currency_code": "EUR",
		"no_note": 1,
		"no_shipping": 1,
		"return": return_url,
		"cancel_return": return_url
	}
	redirect_url = PAYPAL_URL + "?" + urllib.urlencode(args)

	payment = Payment(sponsorship.project_id, sponsorship.sponsorship_id, PaymentGateway.PAYPAL_STANDARD)
	payment.url = redirect_url
	return payment


def process_payment(sponsorship, payment, details):
	"""
	Validates payment
	"""
	transaction_id = details["tx"]

	payload = {
		"cmd": "_notify-synch",
		"at": config.PAYPAL_PDT_ACCESS_TOKEN,
		"tx": transaction_id
	}

	# Check for reused transaction ID
	if db.session.query(db.exists().where(Payment.gateway_id==transaction_id)).scalar():
		return False

	r = requests.post(PAYPAL_URL, data=payload)
	
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
	if retrieved_payment['business'] != config.PAYPAL_RECEIVER_EMAIL:
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


