from bountyfunding.core.const import PaymentGateway
from bountyfunding.core.errors import Error

from bountyfunding.core.payment.dummy import DummyGateway

from bountyfunding.core.payment.paypal_standard import PayPalStandardGateway
from bountyfunding.core.payment.paypal_adaptive import PayPalAdaptiveGateway


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
            raise Error("Unknown payment gateway")


payment_factory = PaymentFactory()
