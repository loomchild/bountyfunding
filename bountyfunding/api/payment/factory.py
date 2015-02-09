from bountyfunding.api.const import PaymentGateway
from bountyfunding.api.errors import APIException

from bountyfunding.api.payment.dummy import DummyGateway

from bountyfunding.api.payment.paypal_standard import PayPalStandardGateway
from bountyfunding.api.payment.paypal_adaptive import PayPalAdaptiveGateway


class PaymentFactory:
    
    def __init__(self):
        self.gateways = {
            PaymentGateway.DUMMY: DummyGateway(),
            PaymentGateway.PAYPAL_STANDARD: PayPalStandardGateway(),
            PaymentGateway.PAYPAL_ADAPTIVE: PayPalAdaptiveGateway(),
        }

    def get_payment_gateway(self, gateway):
        #TODO: check if gateway is active per project
        try:
            return self.gateways[gateway]
        except KeyError:
            raise APIException("Unknown payment gateway")


payment_factory = PaymentFactory()
