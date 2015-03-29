from nose.tools import *

from bountyfunding.core.models import Account


def test_password_setter():
    account = Account("jane@bountyfunding.org", "Jane", 'cat')
    assert account.password_hash is not None

@raises(AttributeError)
def test_no_password_getter():
    account = Account("jane@bountyfunding.org", "Jane", 'cat')
    account.password

def test_password_verification():
    account = Account("jane@bountyfunding.org", "Jane", 'cat')
    assert account.verify_password('cat')
    assert account.verify_password('dog') == False

def test_password_salts_are_random():
    account1 = Account("jane@bountyfunding.org", "Jane", 'cat')
    account2 = Account("john@bountyfunding.org", "John", 'cat')
    assert account1.password_hash != account2.password_hash

def test_empty_password():
    account = Account("jane@bountyfunding.org", "Jane", None)
    assert account.verify_password('cat') == False


