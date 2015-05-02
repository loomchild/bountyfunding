from bountyfunding.util.api import to_object
from nose.tools import *

def test_empty():
    r = to_object({})
    eq_("DictObject", type(r).__name__)

def test_string():
    r = to_object("str")
    eq_("str", r)

def test_number():
    r = to_object(5)
    eq_(5, r)

def test_list():
    r = to_object(["str", 5])
    eq_(["str", 5], r)

def test_object():
    r = to_object({"a": "str", "b" : 5})
    eq_("str", r.a)
    eq_(5, r.b)

def test_recursive_object():
    r = to_object({"a": "str", "b" : 5, "c" : {"c1": 6}, "d": [{"d1": 7}]})
    eq_("str", r.a)
    eq_(5, r.b)
    eq_(6, r.c.c1)
    eq_(7, r.d[0].d1)




