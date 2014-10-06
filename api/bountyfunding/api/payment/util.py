from bountyfunding.api.errors import APIException
from bountyfunding.api.data import retrieve_user
from bountyfunding.api.config import config


def get_paypal_url(project_id):
	if config[project_id].PAYPAL_SANDBOX:
		paypal_url = 'https://www.sandbox.paypal.com'
	else: 
		paypal_url = 'https://www.paypal.com'
	paypal_url += '/cgi-bin/webscr'
	return paypal_url



