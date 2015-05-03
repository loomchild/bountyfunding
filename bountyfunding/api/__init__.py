from flask import Blueprint

api = Blueprint('api', __name__, template_folder='templates')

import bountyfunding.api.views
