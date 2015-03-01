from flask import Blueprint

api = Blueprint('api', __name__)

import bountyfunding.api.views
