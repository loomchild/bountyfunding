import requests
from collections import namedtuple


DEFAULT_API_URL = 'http://localhost:5000'


class Api:

	def __init__(self, token, url=DEFAULT_API_URL):
		self.token = token
		self.url = url

	def call(self, method, path, **kwargs):
		full_url = self.url + path
		params = kwargs
		params['token'] = self.token
		return requests.request(method, full_url, params=params)

	def get(self, path, **kwargs):
		return self.call('GET', path, **kwargs)
	
	def post(self, path, **kwargs):
		return self.call('POST', path, **kwargs)

	def put(self, path, **kwargs):
		return self.call('PUT', path, **kwargs)
	
	def delete(self, path, **kwargs):
		return self.call('DELETE', path, **kwargs)

	#TODO: Add ensure calls that throw an exception if code is not 200/201


def dict_to_object(d):
	o = namedtuple('DictObject', d.keys())(*d.values())
	return o


