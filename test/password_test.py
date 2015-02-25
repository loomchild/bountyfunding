from nose.tools import *

from bountyfunding.api.models import User


def test_password_setter():
    user = User(1, "jane", password='cat')
    assert user.password_hash is not None

@raises(AttributeError)
def test_no_password_getter():
    user = User(1, "jane", password='cat')
    user.password

def test_password_verification():
    user = User(1, "jane", password='cat')
    assert user.verify_password('cat')
    assert user.verify_password('dog') == False

def test_password_salts_are_random():
    user1 = User(1, "jane", password='cat')
    user2 = User(1, "john", password='cat')
    assert user1.password_hash != user2.password_hash

def test_empty_password():
    user = User(1, "jane", password=None)
    assert user.verify_password('cat') == False


