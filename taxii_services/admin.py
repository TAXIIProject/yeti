# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

from django.contrib import admin
from taxii_services.models import DataFeed, MessageBindingId, ContentBindingId, ProtocolBindingId, DataFeedPushMethod, DataFeedPollInformation, DataFeedSubscriptionMethod


class DataFeedAdmin(admin.ModelAdmin):
	list_display = ['id', 'name', 'description']
	
class ProtocolBindingIdAdmin(admin.ModelAdmin):
	list_display = ['title', 'description', 'id', 'binding_id', 'date_created', 'date_updated']

class MessageBindingIdAdmin(admin.ModelAdmin):
	list_display = ['title', 'description', 'id', 'binding_id', 'date_created', 'date_updated']
	
class ContentBindingIdAdmin(admin.ModelAdmin):
	list_display = ['title', 'description', 'id', 'binding_id', 'date_created', 'date_updated']
	
class DataFeedPushMethodAdmin(admin.ModelAdmin):
	pass


admin.site.register(DataFeed, DataFeedAdmin)
admin.site.register(MessageBindingId, MessageBindingIdAdmin)
admin.site.register(ContentBindingId, ContentBindingIdAdmin)
admin.site.register(ProtocolBindingId, ProtocolBindingIdAdmin)
admin.site.register(DataFeedPushMethod, DataFeedPushMethodAdmin)
admin.site.register(DataFeedPollInformation)
admin.site.register(DataFeedSubscriptionMethod)
