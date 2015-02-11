from flask import Flask

app = Flask(__name__)

from bountyfunding.api import api

app.register_blueprint(api)

