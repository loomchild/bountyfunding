from paypalx import AdaptivePayments, PaypalError
from config import config
from models import db, Payment
from const import PaymentGateway


def get_paypal(project_id):
	paypal = AdaptivePayments(
		config[project_id].PAYPAL_USER_ID, 
		config[project_id].PAYPAL_PASSWORD, 
		config[project_id].PAYPAL_SIGNATURE,
		config[project_id].PAYPAL_APPLICATION_ID,
		config[project_id].PAYPAL_RECEIVER_EMAIL,
		config[project_id].PAYPAL_SANDBOX)

	paypal.debug = False
	
	return paypal


#TODO: there's identical method in standard payments - move to common package
def get_paypal_url(project_id):
	if config[project_id].PAYPAL_SANDBOX:
		paypal_url = 'https://www.sandbox.paypal.com'
	else: 
		paypal_url = 'https://www.paypal.com'
	paypal_url += '/cgi-bin/webscr'
	return paypal_url


def create_payment(project_id, sponsorship, return_url):
	receivers = [{'amount': sponsorship.amount, 'email':config[project_id].PAYPAL_RECEIVER_EMAIL}]
    
	paypal = get_paypal(project_id)
	response = paypal.pay(
		actionType='PAY',
		reverseAllParallelPaymentsOnError=True,
		currencyCode="EUR",
		feesPayer='SENDER',
		receiverList={'receiver': receivers},
		returnUrl=return_url,
		cancelUrl=return_url,
	)

	pay_key = response['payKey']
	redirect_url = get_paypal_url(project_id) + '?cmd=_ap-payment&paykey=' + pay_key

	payment = Payment(sponsorship.project_id, sponsorship.sponsorship_id, PaymentGateway.PAYPAL_ADAPTIVE)
	payment.url = redirect_url
	payment.gateway_id = pay_key
	return payment


def process_payment(project_id, sponsorship, payment, details):
	paypal = get_paypal(project_id)
	pay_key = payment.gateway_id
	
	response = paypal.payment_details(
		payKey=pay_key,
	)

	status = response['status']
	return status == 'COMPLETED'


