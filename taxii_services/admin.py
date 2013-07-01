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
from taxii_services.models import DataFeed, MessageBindingId, ContentBindingId, ProtocolBindingId


class DataFeedAdmin(admin.ModelAdmin):
	list_display = ['id', 'name', 'description']
	
class ProtocolBindingIdAdmin(admin.ModelAdmin):
	list_display = ['id', 'binding_id', 'date_created', 'date_updated']

class MessageBindingIdAdmin(admin.ModelAdmin):
	list_display = ['id', 'binding_id', 'date_created', 'date_updated']
	
class ContentBindingIdAdmin(admin.ModelAdmin):
	list_display = ['id', 'binding_id', 'date_created', 'date_updated']
	

admin.site.register(DataFeed, DataFeedAdmin)
admin.site.register(MessageBindingId, MessageBindingIdAdmin)
admin.site.register(ContentBindingId, ContentBindingIdAdmin)
admin.site.register(ProtocolBindingId, ProtocolBindingIdAdmin)
