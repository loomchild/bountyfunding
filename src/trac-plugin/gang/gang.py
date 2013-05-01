from trac.core import *
from trac.util.html import html
from trac.web import IRequestHandler
from trac.web.chrome import INavigationContributor

class GangPlugin(Component):
    implements(ITemplateStreamFilter)

	# ITemplateStreamFilter methods

	def filter_stream(self, req, method, filename, stream, data):
		if filename == 'ticket.html':
			ticket = data.get('ticket')
            if ticket and ticket.exists:
				filter = Transformer('.//body')
				stream |= filter.append(" somebody to love..."))
		return stream

