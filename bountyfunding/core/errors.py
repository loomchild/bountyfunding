class Error(Exception):
    def __init__(self, message=""):
        self.message = message

class SecurityError(Exception):
    def __init__(self, message=""):
        self.message = message

class ExternalApiError(Exception):
    
    def __init__(self, message="", status_code=None, reason=None):
        self.message = message
        self.status_code = status_code
        self.reason = reason

    def __str__(self):
        message = self.message
        if self.status_code != None:
            message += "; code = %s" % self.status_code
        if self.reason != None:
            message += "; reason = %s" % self.reason
        return message

class GithubError(ExternalApiError):
    
    def __init__(self, message="", result=None):
        self.message = message
        if result != None:
            self.status_code = result.status_code
            self.reason = result.json().get("message")

    def __str__(self):
        return super(GithubError, self).__str__()



