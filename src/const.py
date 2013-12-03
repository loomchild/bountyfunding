from enum import Enum

class IssueStatus(Enum):
	READY = 10
	STARTED = 20
	COMPLETED = 30

class SponsorshipStatus(Enum):
	PLEDGED = 10
	CONFIRMED = 20
	VALIDATED = 30

class PaymentStatus(Enum):
	INITIATED = 10
	CONFIRMED = 20

class PaymentGateway(Enum):
	PLAIN = 10
	PAYPAL_REST = 20
	PAYPAL_STANDARD = 21


