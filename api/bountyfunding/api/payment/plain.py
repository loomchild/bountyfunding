from bountyfunding.api.const import PaymentGateway
from bountyfunding.api.models import Payment

import re

DATE_PATTERN = re.compile('^(0?[1-9]|1[012])/[0-9][0-9]$')


class PlainGateway:

	def create_payment(self, project_id, sponsorship, return_url):
		payment = Payment(project_id, sponsorship.sponsorship_id, PaymentGateway.PLAIN)
		return payment

	def process_payment(self, project_id, sponsorship, payment, details):
		card_number = details.get('card_number')
		card_date = details.get('card_date')
		if card_number != '4111111111111111' or DATE_PATTERN.match(card_date) == None:
			return False
		return True

