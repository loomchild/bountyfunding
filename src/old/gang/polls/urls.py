from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from polls.models import Poll

urlpatterns = patterns('',
    url(r'^$', ListView.as_view(queryset=Poll.objects.order_by('-pub_date')[:5])),
    url(r'^(?P<pk>\d+)/$', DetailView.as_view(model=Poll)),
    url(r'^(?P<pk>\d+)/results/$', DetailView.as_view(model=Poll, template_name='polls/results.html'),
        name='poll_results'),
    url(r'^(?P<poll_id>\d+)/vote/$', 'polls.views.vote'),
)
