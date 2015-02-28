from collections import namedtuple

import flask
import requests
from flask.json import loads


def to_dict(sth, path=None):
    if isinstance(sth, flask.Response):
        sth = loads(sth.data)
    if isinstance(sth, requests.Response):
        sth = sth.json()
    if path:
        sth = sth.get(path)
    return sth
 
def to_object(sth, path=None):
    sth = to_dict(sth, path)
    if isinstance(sth, list):
        obj = [_dict_to_object(s) for s in sth]
    else:
        obj = _dict_to_object(sth)
    return obj

def _dict_to_object(d):
    return namedtuple('DictObject', d.keys())(*d.values())


