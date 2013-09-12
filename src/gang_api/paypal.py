import sys, requests, json

import logging, httplib
httplib.HTTPConnection.debuglevel = 1
logging.basicConfig() 
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

PAYPAL_API_BASE_URL = 'https://svcs.sandbox.paypal.com/AdaptivePayments'
PAYPAL_PAY_URL = PAYPAL_API_BASE_URL + '/Pay'
PAYPAL_PAYMENT_DETAILS_URL = PAYPAL_API_BASE_URL + '/PaymentDetails'
PAYPAL_CERTIFICATE_VERIFY=False

PAYPAL_AUTHORIZE_BASE_URL = 'https://www.sandbox.paypal.com/cgi-bin/webscr'
PAYPAL_AUTHORIZE_URL = PAYPAL_AUTHORIZE_BASE_URL + '?cmd=_ap-payment&paykey='

PAYPAL_USERID = 'paypal-business_api1.gangfunding.org'
PAYPAL_PASSWORD = '1377898278'
PAYPAL_SIGNATURE = 'A--8MSCLabuvN8L.-MHjxC9uypBtAfV2vPwxoeI5CcF5duvwRtSUR.AO'
PAYPAL_APPLICATIONID = 'APP-80W284485P519543T'
PAYPAL_RECEIVER_EMAIL = 'paypal-business@gangfunding.org'

HEADERS = {
	"X-PAYPAL-SECURITY-USERID": PAYPAL_USERID,
	"X-PAYPAL-SECURITY-PASSWORD": PAYPAL_PASSWORD,
	"X-PAYPAL-SECURITY-SIGNATURE": PAYPAL_SIGNATURE,
	"X-PAYPAL-APPLICATION-ID": PAYPAL_APPLICATIONID,
	"X-PAYPAL-REQUEST-DATA-FORMAT": "JSON",
	"X-PAYPAL-RESPONSE-DATA-FORMAT": "JSON"
}


def create_payment(amount, return_url):
	"""
	Returns authorization URL
	"""
	url = PAYPAL_PAY_URL
	payload = {
		"actionType": "PAY",
		"currencyCode": "EUR",
		"receiverList": {
			"receiver": [
				{"amount": str(amount), "email": PAYPAL_RECEIVER_EMAIL}
			]
		},
		"returnUrl": return_url,
		"cancelUrl": return_url,
		"requestEnvelope": {
			"errorLanguage": "en_US",
			"detailLevel": "ReturnAll"
		}
	}
	
	response = requests.post(url, data=json.dumps(payload), headers=HEADERS, 
			verify=PAYPAL_CERTIFICATE_VERIFY)
	
	print(response.json())

	pay_key = response.json()["payKey"]
	return pay_key

def get_authorization_url(pay_key):
	authorization_url = PAYPAL_AUTHORIZE_URL + pay_key
	return authorization_url

def is_payment_completed(pay_key):
	"""
	Retrieves payment status
	"""
	url = PAYPAL_PAYMENT_DETAILS_URL
	payload = {
		"payKey": pay_key,
		"requestEnvelope": {
			"errorLanguage": "en_US",
			"detailLevel": "ReturnAll"
		}
	}

	response = requests.post(url, data=json.dumps(payload), headers=HEADERS, 
			verify=PAYPAL_CERTIFICATE_VERIFY)
	
	print(response.json())
	
	status = response.json()["status"]
	
	return status == 'COMPLETED'

