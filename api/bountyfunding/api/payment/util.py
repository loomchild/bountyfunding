from bountyfunding.api.errors import APIException
from bountyfunding.api.data import retrieve_user
from bountyfunding.api.config import config


def retrieve_admin(project_id):
	admin = retrieve_user(project_id, config[project_id].ADMIN)
	if admin == None or admin.paypal_email == None:
		raise APIException('Admin does not exist or does not have PayPal email', 500)

	return admin


def get_paypal_url(project_id):
	if config[project_id].PAYPAL_SANDBOX:
		paypal_url = 'https://www.sandbox.paypal.com'
	else: 
		paypal_url = 'https://www.paypal.com'
	paypal_url += '/cgi-bin/webscr'
	return paypal_url



