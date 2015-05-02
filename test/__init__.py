from flask.json import loads
from bountyfunding.util.api import to_object as json_to_object


def to_object(response):
    return json_to_object(loads(response.data))

