from os import path
from flask import Flask

app = Flask(__name__)

BOUNTYFUNDING_HOME=path.abspath(path.join(path.dirname(path.abspath(__file__)), '..', '..'))

import bountyfunding_api.views
