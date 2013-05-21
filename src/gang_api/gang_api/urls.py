from django.conf.urls import patterns, include, url

from gang_api.api import IssueResource

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

issue_resource = IssueResource()

urlpatterns = patterns('',
	(r'^', include(issue_resource.urls)),
    # Examples:
    # url(r'^$', 'gang_api.views.home', name='home'),
    # url(r'^gang_api/', include('gang_api.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
