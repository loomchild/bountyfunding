import paypalrestsdk

import httplib2
httplib2.debuglevel = 1

import config

paypalrestsdk.configure({
  "mode": config.PAYPAL_MODE,
  "client_id": config.PAYPAL_CLIENT_ID,
  "client_secret": config.PAYPAL_CLIENT_SECRET })


def create_payment(amount, return_url):
	"""
	Returns authorization URL
	"""
	payment = paypalrestsdk.Payment({
		"intent": "sale",
		"payer": {
			"payment_method": "paypal",
		},
		"transactions": [{
    		"amount": {
				"total": "%d.00" % amount,
				"currency": "EUR", 
			},
			"item_list": { 
				"items":[{
                        "quantity": "1", 
                        "name": "BountyFunding deposit", 
                        "price": "%d.00" % amount,  
                        "currency":"EUR"
				}]
            },
		}],
		"redirect_urls": {
			"return_url": return_url,
			"cancel_url": return_url,
		},
	})

	if payment.create():
		payment_id = payment.id
		payment_url = filter(lambda link : link.rel == 'approval_url', payment.links)[0].href
		#print(payment_url)
		return payment_id, payment_url
	else:
		print payment.error
		return None

def execute_payment(payment_id, payer_id):
	payment = paypalrestsdk.Payment.find(payment_id)
	payment.execute({"payer_id": payer_id})
	return payment.state == 'approved'

def is_payment_completed(payment_id):
	"""
	Retrieves payment status
	"""
	payment = paypalrestsdk.Payment.find(payment_id)
	#print payment
	return payment.state == 'approved'

