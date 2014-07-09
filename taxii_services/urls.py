# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^inbox/?$', 'taxiiweb.views.service_router'),
    url(r'^poll/?$', 'taxiiweb.views.service_router'),
    url(r'^query_example/?$', 'taxiiweb.views.service_router'),
    url(r'^discovery/?$', 'taxiiweb.views.service_router'),
)
