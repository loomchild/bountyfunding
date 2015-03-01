class Error(Exception):
    def __init__(self, message=""):
        self.message = message

class SecurityError(Exception):
    def __init__(self, message=""):
        self.message = message

