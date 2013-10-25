from enum import Enum

class SponsorshipStatus(Enum):
	PLEDGED = 10
	CONFIRMED = 20
	VALIDATED = 30

class PaymentStatus(Enum):
	INITIATED = 10
	CONFIRMED = 20

class PaymentGateway(Enum):
	PLAIN = 10
	PAYPAL = 20


