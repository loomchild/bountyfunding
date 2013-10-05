from os import path
import ConfigParser
from homer import BOUNTYFUNDING_HOME

CONFIG_FILE = path.abspath(path.join(BOUNTYFUNDING_HOME, 'conf', 'bountyfunding_api.ini'))

parser = ConfigParser.RawConfigParser()
parser.readfp(open(CONFIG_FILE))

TRACKER_URL = parser.get('general', 'tracker_url')

