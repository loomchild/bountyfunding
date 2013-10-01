from os import path
from flask import Flask

app = Flask(__name__)

GANG_HOME=path.abspath(path.join(path.dirname(path.abspath(__file__)), '..', '..'))

import gang_api.views
