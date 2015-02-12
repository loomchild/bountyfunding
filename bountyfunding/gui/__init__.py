from flask import Blueprint

gui = Blueprint('gui', __name__, template_folder='templates')

import bountyfunding.gui.views

