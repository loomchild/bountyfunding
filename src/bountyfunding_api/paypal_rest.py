import paypalrestsdk

import httplib2
httplib2.debuglevel = 1

import config
from models import Payment
from const import PaymentGateway

def init_sdk():
	if config.PAYPAL_SANDBOX:
		mode = 'sandbox'
	else:
		mode = 'live' 

	paypalrestsdk.configure({
	  "mode": mode,
	  "client_id": config.PAYPAL_CLIENT_ID,
	  "client_secret": config.PAYPAL_CLIENT_SECRET })


def create_payment(sponsorship, return_url):
	"""
	Returns authorization URL
	"""
	created_payment = paypalrestsdk.Payment({
		"intent": "sale",
		"payer": {
			"payment_method": "paypal",
		},
		"transactions": [{
    		"amount": {
				"total": "%d.00" % sponsorship.amount,
				"currency": "EUR", 
			},
			"item_list": { 
				"items":[{
                        "quantity": "1", 
                        "name": "BountyFunding deposit", 
                        "price": "%d.00" % sponsorship.amount,  
                        "currency":"EUR"
				}]
            },
		}],
		"redirect_urls": {
			"return_url": return_url,
			"cancel_url": return_url,
		},
	})

	if created_payment.create():
		payment_url = filter(lambda link : link.rel == 'approval_url', created_payment.links)[0].href

		payment = Payment(sponsorship.project_id, sponsorship.sponsorship_id, PaymentGateway.PAYPAL_REST)
		payment.gateway_id = created_payment.id
		payment.url = payment_url
		return payment
	else:
		print payment.error
		return None


def process_payment(sponsorship, payment, details):
	payer_id = details.get('PayerID')
	retrieved_payment = paypalrestsdk.Payment.find(payment.gateway_id)
	retrieved_payment.execute({"payer_id": payer_id})
	# TODO: Validate details otherwise someone can reuse a transaction
	return retrieved_payment.state == 'approved'


init_sdk()
