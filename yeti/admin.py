# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file


from django.contrib import admin
from django.utils.html import format_html

from yeti.models import Certificate

class CertificateAdmin(admin.ModelAdmin):
    list_display = ['id','title','subject','issuer','description', 'cert']
    
    def cert(self, obj):
        return format_html(u'<pre>{0}</pre>', obj.pem_certificate)
    
    cert.allow_tags = True
    
    pass

admin.site.register(Certificate, CertificateAdmin)
