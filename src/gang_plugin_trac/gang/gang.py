from pprint import pprint

from genshi.filters import Transformer
from genshi.builder import tag

from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor
from trac.web.api import ITemplateStreamFilter

import requests

API_URL='http://localhost:5000'

class GangPlugin(Component):
	implements(ITemplateStreamFilter)

	# ITemplateStreamFilter methods

	def filter_stream(self, req, method, filename, stream, data):
		"""
		Quick and dirty solution - modify page on the fly to inject special field. It would be
		much nicer if we can do it by creating custom field as this depends on page structure.
		"""
		if filename == 'ticket.html':
			ticket = data.get('ticket')
			if ticket and ticket.exists:
				identifier = ticket.id
				url = API_URL + '/issue/%s' % identifier
				request = requests.get(url)
				amount = request.json().get('amount', 0)

				#Alternatively add custom field to ticket object
				pprint (vars(ticket))
				filter = Transformer('.//table[@class="properties"]	')
				stream |= filter.append(tag.tr(tag.th(" Gang: ", id="h_gang"), tag.td(u"%d\u20ac" % amount, headers="h_gang")))
		return stream

