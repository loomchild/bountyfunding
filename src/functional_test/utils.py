import requests

# TODO: Covert to SDK and use in plugins
class Api:

	def __init__(self, url):
		self.url = url

	def call(self, method, path, **kwargs):
		full_url = self.url + path
		return requests.request(method, full_url, params=kwargs)

	def get(self, path, **kwargs):
		return self.call('GET', path, **kwargs)
	
	def post(self, path, **kwargs):
		return self.call('POST', path, **kwargs)

	def put(self, path, **kwargs):
		return self.call('PUT', path, **kwargs)
	
	def delete(self, path, **kwargs):
		return self.call('DELETE', path, **kwargs)


API_URL = 'http://localhost:5000'
api = Api(API_URL)
