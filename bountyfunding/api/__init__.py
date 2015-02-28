from flask import Blueprint

api = Blueprint('api', __name__)

# Force config to be loaded before database due to circular dependency
import bountyfunding.api.config

import bountyfunding.api.views
