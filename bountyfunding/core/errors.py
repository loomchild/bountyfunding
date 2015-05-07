class Error(Exception):
    def __init__(self, message=""):
        self.message = message

class SecurityError(Exception):
    def __init__(self, message=""):
        self.message = message

class ExternalApiError(Exception):
    
    def __init__(self, message, url, method, path, status_code=None, reason=None):
        self.message = message
        self.url = url
        self.method = method
        self.path = path
        self.status_code = status_code
        self.reason = reason

    def __str__(self):
        message = "%s %s%s: %s" % (self.method, self.url, self.path, self.message)
        if self.status_code != None:
            message += ", code = %s" % self.status_code
        if self.reason != None:
            message += ", reason = %s" % self.reason
        return message

