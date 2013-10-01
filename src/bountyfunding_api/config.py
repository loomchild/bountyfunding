import ConfigParser
from os import path

GANG_HOME = path.dirname(path.abspath(__file__))
CONFIG_FILE = path.abspath(path.join(GANG_HOME, '..', '..', 'conf', 'gang_api.ini'))

parser = ConfigParser.RawConfigParser()
parser.readfp(open(CONFIG_FILE))

TRACKER_URL = parser.get('general', 'tracker_url')

