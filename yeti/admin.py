######################################################################################
#                                                                                    #
# Copyright (C) 2012-2013 - The MITRE Corporation. All Rights Reserved.              #
#                                                                                    #
# By using the software, you signify your aceptance of the terms and                 #
# conditions of use. If you do not agree to these terms, do not use the software.    #
#                                                                                    #
# For more information, please refer to the license.txt file.                        #
#                                                                                    #
######################################################################################

from django.contrib import admin

from yeti.models import Certificate

class CertificateAdmin(admin.ModelAdmin):
	list_display = ['id','title','subject','issuer','description', 'cert']
	
	def cert(self, obj):
		return '<pre>%s</pre>' % obj.pem_certificate
	
	cert.allow_tags = True
	
	pass

admin.site.register(Certificate, CertificateAdmin)
