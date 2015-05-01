from bountyfunding.core.config import config

config.init(dict(config_file="", db_in_memory=True))
#To enable testing with real database replace with config.init(dict())

from bountyfunding.core.data import create_database

create_database()
