from tastypie.resources import ModelResource
from gang_api.models import Issue

class IssueResource(ModelResource):
	class Meta:
		resource_name = 'issue'
		queryset = Issue.objects.all()
		#default_format = 'application/json'

	def determine_format(self, request):
		return 'application/json'
