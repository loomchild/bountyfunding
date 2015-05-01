import requests

class Api(object):

    def __init__(self, url, params={}, headers={}):
        self.url = url
        self.params = params
        self.headers = headers

    def call(self, method, path, **kwargs):
        full_url = self.url + path

        params = {}
        params.update(self.params)
        params.update(kwargs)
        
        headers = self.headers
        
        return requests.request(method, full_url, params=params, headers=headers)

    def get(self, path, **kwargs):
        return self.call('GET', path, **kwargs)
    
    def post(self, path, **kwargs):
        return self.call('POST', path, **kwargs)

    def put(self, path, **kwargs):
        return self.call('PUT', path, **kwargs)
    
    def delete(self, path, **kwargs):
        return self.call('DELETE', path, **kwargs)



class BountyFundingApi(Api):
    
    def __init__(self, url='http://localhost:8080', token=None):
        super(BountyFundingApi, self).__init__(url, dict(token=token))


