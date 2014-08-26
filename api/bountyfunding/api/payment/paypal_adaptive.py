from paypalx import AdaptivePayments, PaypalError

from bountyfunding.api.config import config
from bountyfunding.api.models import db, Payment
from bountyfunding.api.errors import APIException
from bountyfunding.api.data import retrieve_user
from bountyfunding.api.const import PaymentGateway
from bountyfunding.api.payment.util import retrieve_admin, get_paypal_url



class PayPalAdaptiveGateway:

	def create_payment(self, project_id, sponsorship, return_url):
		if not return_url:
			raise APIException('return_url cannot be blank', 400)

		admin = retrieve_admin(project_id)
		
		receivers = [{'amount': sponsorship.amount, 'email': admin.paypal_email}]
		
		paypal = self.get_paypal(project_id)
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

		payment = Payment(sponsorship.project_id, sponsorship.sponsorship_id, PaymentGateway.PAYPAL_ADAPTIVE, admin.user_id)
		payment.url = redirect_url
		payment.gateway_id = pay_key
		return payment

	def process_payment(self, project_id, sponsorship, payment, details):
		paypal = self.get_paypal(project_id)
		pay_key = payment.gateway_id
		
		response = paypal.payment_details(
			payKey=pay_key,
		)

		status = response['status']
		return status == 'COMPLETED'

	def get_paypal(self, project_id):
		paypal = AdaptivePayments(
			config[project_id].PAYPAL_USER_ID, 
			config[project_id].PAYPAL_PASSWORD, 
			config[project_id].PAYPAL_SIGNATURE,
			config[project_id].PAYPAL_APPLICATION_ID,
			config[project_id].PAYPAL_RECEIVER_EMAIL,
			config[project_id].PAYPAL_SANDBOX)

		paypal.debug = False
		
		return paypal

