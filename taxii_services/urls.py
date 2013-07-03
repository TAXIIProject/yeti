# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'yeti.views.home', name='home'),
    # url(r'^yeti/', include('yeti.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    
    url(r'^inbox/$', 'taxii_services.inbox_service'),
    url(r'^inbox/(?P<dest_feed_name>\s+)/$', 'taxii_services.inbox_service'),
)
