from utils import Api, dict_to_object
from const import *
from nose.tools import *


PROJECT_ID = -1;
USER = 'loomchild'
CARD_NUMBER = "4111111111111111"
CARD_DATE = "05/50"


api = Api(PROJECT_ID)


def teardown():
	r = api.delete('/')
	eq_(r.status_code, 200)


def test_sponsorship_pledged_transitions():
	yield TransitionCheck(sponsorship_pledged, sponsorship_pledged, 409)
	yield TransitionCheck(sponsorship_pledged, payment_initiated, 200)
	yield TransitionCheck(sponsorship_pledged, payment_confirmed, 404)
	yield TransitionCheck(sponsorship_pledged, sponsorship_validated, 403)
	yield TransitionCheck(sponsorship_pledged, sponsorship_deleted, 200)

def test_payment_initiated_transitions():
	yield TransitionCheck(payment_initiated, sponsorship_pledged, 409)
	yield TransitionCheck(payment_initiated, payment_initiated, 200)
	yield TransitionCheck(payment_initiated, payment_confirmed, 200)
	yield TransitionCheck(payment_initiated, sponsorship_validated, 403)
	yield TransitionCheck(payment_initiated, sponsorship_deleted, 200)

def test_payment_confirmed_transitions():
	yield TransitionCheck(payment_confirmed, sponsorship_pledged, 409)
	yield TransitionCheck(payment_confirmed, payment_initiated, 403)
	yield TransitionCheck(payment_confirmed, payment_confirmed, 403)
	yield TransitionCheck(payment_confirmed, sponsorship_validated, 200)
	yield TransitionCheck(payment_confirmed, sponsorship_deleted, 403)

def test_sponsorship_validated_transitions():
	yield TransitionCheck(sponsorship_validated, sponsorship_pledged, 409)
	yield TransitionCheck(sponsorship_validated, payment_initiated, 403)
	yield TransitionCheck(sponsorship_validated, payment_confirmed, 403)
	yield TransitionCheck(sponsorship_validated, sponsorship_validated, 403)
	yield TransitionCheck(sponsorship_validated, sponsorship_deleted, 403)


def test_can_only_change_sponsorship_status_to_validated():
	"""
	Checks whether sponsorship status accepts only VALIDATED parameter
	"""
	eq_(sponsorship_pledged().status_code, 200)

	eq_(sponsorship_change_status(SponsorshipStatus.PLEDGED).status_code, 400)
	eq_(sponsorship_change_status(SponsorshipStatus.CONFIRMED).status_code, 400)

	eq_(payment_initiated().status_code, 200)
	eq_(payment_confirmed().status_code, 200)

	eq_(sponsorship_change_status(SponsorshipStatus.PLEDGED).status_code, 400)
	eq_(sponsorship_change_status(SponsorshipStatus.CONFIRMED).status_code, 400)

	eq_(sponsorship_validated().status_code, 200)

	eq_(sponsorship_change_status(SponsorshipStatus.PLEDGED).status_code, 400)
	eq_(sponsorship_change_status(SponsorshipStatus.CONFIRMED).status_code, 400)


def sponsorship_pledged():
	return api.post('/issue/1/sponsorships', user=USER, amount=10)

def payment_initiated():
	return api.post('/issue/1/sponsorship/%s/payments' % USER, gateway=PaymentGateway.to_string(PaymentGateway.PLAIN))

def payment_confirmed():
	return api.put('/issue/1/sponsorship/%s/payment' % USER, status=PaymentStatus.to_string(PaymentStatus.CONFIRMED), card_number=CARD_NUMBER, card_date=CARD_DATE)

def sponsorship_validated():
	return sponsorship_change_status(SponsorshipStatus.VALIDATED)

def sponsorship_change_status(status):
	return api.put('/issue/1/sponsorship/%s' % USER, status=SponsorshipStatus.to_string(status))

def sponsorship_deleted():
	return api.delete('/issue/1/sponsorship/%s' % USER)


class TransitionCheck:

	STATES = [sponsorship_pledged, payment_initiated, payment_confirmed, sponsorship_validated]

	def __init__(self, old_state, new_state, status_code):
		"""
		Create a transition test and set a nice description
		"""
		self.old_state = old_state
		self.new_state = new_state
		self.status_code = status_code
		self.description = "Transition %s -> %s" % (old_state.__name__, new_state.__name__)

	def __call__(self):
		"""
		Transition from old state to new state and check returned status code.
		"""
		# Setup a state by executing of all transitions before it
		for state in TransitionCheck.STATES:
			state()
			if state == self.old_state:
				break
		
		r = self.new_state()

		if r.status_code != self.status_code:
			error = "%i != %i" % (r.status_code, self.status_code)
			error_message = r.json().get('error')
			if error_message != None:
				error += ": " + error_message
			eq_(r.status_code, self.status_code, error)
		
		teardown()
