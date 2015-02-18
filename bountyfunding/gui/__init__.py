from flask import Blueprint

gui = Blueprint('gui', __name__, template_folder='templates', 
        static_folder='static', static_url_path='/static/gui')

import bountyfunding.gui.views

