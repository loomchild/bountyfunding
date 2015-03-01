import bountyfunding
from bountyfunding.core.const import *
from bountyfunding.core.data import create_database

from test import to_dict, to_object

from nose.tools import *


USER = 'loomchild'
CARD_NUMBER = "4111111111111111"
CARD_DATE = "05/50"


app = None

class State_Test:

    def setup(self):
        global app
        app = bountyfunding.app.test_client()
        create_database()

    def test_change_sponsorship_status_to_invalid_status(self):
        """
        Checks whether sponsorship status does not accept pledged and confirmed states
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

        eq_(sponsorship_rejected().status_code, 200)
        
        eq_(sponsorship_change_status(SponsorshipStatus.PLEDGED).status_code, 400)
        eq_(sponsorship_change_status(SponsorshipStatus.CONFIRMED).status_code, 400)

    def test_can_change_amount_only_in_pledged_state(self):
        check_response(sponsorship_pledged(), 200)
        check_response(sponsorship_change_amount(15), 200)
        
        check_response(payment_initiated(), 200)
        check_response(sponsorship_change_amount(20), 200)
        
        check_response(payment_confirmed(), 200)
        check_response(sponsorship_change_amount(20), 403)
        
        check_response(sponsorship_rejected(), 200)
        check_response(sponsorship_change_amount(20), 403)
        
        check_response(sponsorship_validated(), 200)
        check_response(sponsorship_change_amount(20), 403)
        
        check_response(sponsorship_transferred(), 200)
        check_response(sponsorship_change_amount(20), 403)

    def test_sponsorship_pledged_transitions(self):
        yield TransitionCheck(sponsorship_pledged, sponsorship_pledged, 409)
        yield TransitionCheck(sponsorship_pledged, payment_initiated, 200)
        yield TransitionCheck(sponsorship_pledged, payment_confirmed, 404)
        yield TransitionCheck(sponsorship_pledged, sponsorship_validated, 403)
        yield TransitionCheck(sponsorship_pledged, sponsorship_transferred, 403)
        yield TransitionCheck(sponsorship_pledged, sponsorship_rejected, 403)
        yield TransitionCheck(sponsorship_pledged, sponsorship_refunded, 403)
        yield TransitionCheck(sponsorship_pledged, sponsorship_deleted, 200)

    def test_payment_initiated_transitions(self):
        yield TransitionCheck(payment_initiated, sponsorship_pledged, 409)
        yield TransitionCheck(payment_initiated, payment_initiated, 200)
        yield TransitionCheck(payment_initiated, payment_confirmed, 200)
        yield TransitionCheck(payment_initiated, sponsorship_validated, 403)
        yield TransitionCheck(payment_initiated, sponsorship_transferred, 403)
        yield TransitionCheck(payment_initiated, sponsorship_rejected, 403)
        yield TransitionCheck(payment_initiated, sponsorship_refunded, 403)
        yield TransitionCheck(payment_initiated, sponsorship_deleted, 200)

    def test_payment_confirmed_transitions(self):
        yield TransitionCheck(payment_confirmed, sponsorship_pledged, 409)
        yield TransitionCheck(payment_confirmed, payment_initiated, 403)
        yield TransitionCheck(payment_confirmed, payment_confirmed, 403)
        yield TransitionCheck(payment_confirmed, sponsorship_validated, 200)
        yield TransitionCheck(payment_confirmed, sponsorship_transferred, 403)
        yield TransitionCheck(payment_confirmed, sponsorship_rejected, 200)
        yield TransitionCheck(payment_confirmed, sponsorship_refunded, 403)
        yield TransitionCheck(payment_confirmed, sponsorship_deleted, 403)

    def test_sponsorship_validated_transitions(self):
        yield TransitionCheck(sponsorship_validated, sponsorship_pledged, 409)
        yield TransitionCheck(sponsorship_validated, payment_initiated, 403)
        yield TransitionCheck(sponsorship_validated, payment_confirmed, 403)
        yield TransitionCheck(sponsorship_validated, sponsorship_validated, 403)
        yield TransitionCheck(sponsorship_validated, sponsorship_transferred, 200)
        yield TransitionCheck(sponsorship_validated, sponsorship_rejected, 200)
        yield TransitionCheck(sponsorship_validated, sponsorship_refunded, 403)
        yield TransitionCheck(sponsorship_validated, sponsorship_deleted, 403)

    def test_sponsorship_transferred_transitions(self):
        yield TransitionCheck(sponsorship_transferred, sponsorship_pledged, 409)
        yield TransitionCheck(sponsorship_transferred, payment_initiated, 403)
        yield TransitionCheck(sponsorship_transferred, payment_confirmed, 403)
        yield TransitionCheck(sponsorship_transferred, sponsorship_validated, 403)
        yield TransitionCheck(sponsorship_transferred, sponsorship_transferred, 403)
        yield TransitionCheck(sponsorship_transferred, sponsorship_rejected, 403)
        yield TransitionCheck(sponsorship_transferred, sponsorship_refunded, 403)
        yield TransitionCheck(sponsorship_transferred, sponsorship_deleted, 403)

    def test_sponsorship_rejected_transitions(self):
        yield TransitionCheck(sponsorship_rejected, sponsorship_pledged, 409)
        yield TransitionCheck(sponsorship_rejected, payment_initiated, 403)
        yield TransitionCheck(sponsorship_rejected, payment_confirmed, 403)
        yield TransitionCheck(sponsorship_rejected, sponsorship_validated, 200)
        yield TransitionCheck(sponsorship_rejected, sponsorship_transferred, 403)
        yield TransitionCheck(sponsorship_rejected, sponsorship_rejected, 403)
        yield TransitionCheck(sponsorship_rejected, sponsorship_refunded, 200)
        yield TransitionCheck(sponsorship_rejected, sponsorship_deleted, 403)

    def test_sponsorship_refunded_transitions(self):
        yield TransitionCheck(sponsorship_refunded, sponsorship_pledged, 409)
        yield TransitionCheck(sponsorship_refunded, payment_initiated, 403)
        yield TransitionCheck(sponsorship_refunded, payment_confirmed, 403)
        yield TransitionCheck(sponsorship_refunded, sponsorship_validated, 403)
        yield TransitionCheck(sponsorship_refunded, sponsorship_transferred, 403)
        yield TransitionCheck(sponsorship_refunded, sponsorship_rejected, 403)
        yield TransitionCheck(sponsorship_refunded, sponsorship_refunded, 403)
        yield TransitionCheck(sponsorship_refunded, sponsorship_deleted, 403)

    def test_get_path(self):
        eq_(get_path(sponsorship_pledged), [sponsorship_pledged])
        eq_(get_path(sponsorship_validated), 
            [sponsorship_pledged, payment_initiated, payment_confirmed, sponsorship_validated])
        eq_(get_path(sponsorship_refunded), 
            [sponsorship_pledged, payment_initiated, payment_confirmed, sponsorship_rejected, 
            sponsorship_refunded])

class TransitionCheck:

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
        path = get_path(self.old_state)
        for state in path:
            state()
        
        r = self.new_state()

        check_response(r, self.status_code)


def sponsorship_pledged():
    app.put('/user/admin', data=dict(paypal_email='a@b.com'))
    app.post('/issues', data=dict(ref=1, title='Title1', link='/issue/1', 
        status=IssueStatus.to_string(IssueStatus.READY)))
    return app.post('/issue/1/sponsorships', data=dict(user=USER, amount=10))

def payment_initiated():
    return app.post('/issue/1/sponsorship/%s/payments' % USER, data=dict(
        gateway=PaymentGateway.to_string(PaymentGateway.DUMMY)))

def payment_confirmed():
    return app.put('/issue/1/sponsorship/%s/payment' % USER, data=dict(
        status=PaymentStatus.to_string(PaymentStatus.CONFIRMED), 
        card_number=CARD_NUMBER, card_date=CARD_DATE))

def sponsorship_validated():
    return sponsorship_change_status(SponsorshipStatus.VALIDATED)

def sponsorship_rejected():
    return sponsorship_change_status(SponsorshipStatus.REJECTED)

def sponsorship_transferred():
    return sponsorship_change_status(SponsorshipStatus.TRANSFERRED)

def sponsorship_refunded():
    return sponsorship_change_status(SponsorshipStatus.REFUNDED)

def sponsorship_deleted():
    return app.delete('/issue/1/sponsorship/%s' % USER)

def sponsorship_change_status(status):
    return app.put('/issue/1/sponsorship/%s' % USER, data=dict(
        status=SponsorshipStatus.to_string(status)))

def sponsorship_change_amount(amount):
    return app.put('/issue/1/sponsorship/%s' % USER, data=dict(amount=amount))
    
# Mapping between each state and its predecessor in the shortest path. 
STATES = {
    sponsorship_pledged : None,
    payment_initiated : sponsorship_pledged,
    payment_confirmed : payment_initiated,
    sponsorship_validated : payment_confirmed,
    sponsorship_transferred : sponsorship_validated,
    sponsorship_rejected : payment_confirmed,
    sponsorship_refunded : sponsorship_rejected,
}

def get_path(state):
    """
    Returns path to the given state.
    """
    prev_state = STATES[state]
    if prev_state == None:
        return [state]
    else:
        path = get_path(prev_state)
        path.append(state)
        return path		
        
def check_response(response, status_code):
    if response.status_code != status_code:
        error = "%i != %i" % (response.status_code, status_code)
        error_message = response.json().get('error')
        if error_message != None:
            error += ": " + error_message
        eq_(response.status_code, status_code, error)
    

