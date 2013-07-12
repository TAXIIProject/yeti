# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^inbox/(\w+)/$', 'taxii_services.views.inbox_service'),
    url(r'^poll/$', 'taxii_services.views.poll_service'),
)
