# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file


from django.contrib import admin

from yeti.models import Certificate

class CertificateAdmin(admin.ModelAdmin):
	list_display = ['id','title','subject','issuer','description', 'cert']
	
	def cert(self, obj):
		return '<pre>%s</pre>' % obj.pem_certificate
	
	cert.allow_tags = True
	
	pass

admin.site.register(Certificate, CertificateAdmin)
