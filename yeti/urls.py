# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^services/', include('taxii_services.urls')),
    #url(r'^test/', 'taxii_services.views.test')
)

