# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^inbox/(\w+)/$', 'taxii_services.views.inbox_service'),
    url(r'^poll/$', 'taxii_services.views.poll_service'),
    url(r'^discovery/$', 'taxii_services.views.discovery_service'),
)
