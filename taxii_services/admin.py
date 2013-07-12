# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

from django.contrib import admin
from taxii_services.models import Inbox, DataFeed, MessageBindingId, ContentBindingId, ContentBlock, ProtocolBindingId, DataFeedPushMethod, DataFeedPollInformation, DataFeedSubscriptionMethod

class DataFeedAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    
class ProtocolBindingIdAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'id', 'binding_id', 'date_created', 'date_updated']

class MessageBindingIdAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'id', 'binding_id', 'date_created', 'date_updated']
    
class ContentBindingIdAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'id', 'binding_id', 'date_created', 'date_updated']

class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'description', 'timestamp_label','submitted_by', 'message_id', 'content_binding', 'content', 'padding', 'date_created', 'date_updated']

admin.site.register(Inbox)
admin.site.register(DataFeed, DataFeedAdmin)
admin.site.register(ContentBlock, ContentBlockAdmin)
admin.site.register(MessageBindingId, MessageBindingIdAdmin)
admin.site.register(ContentBindingId, ContentBindingIdAdmin)
admin.site.register(ProtocolBindingId, ProtocolBindingIdAdmin)
admin.site.register(DataFeedPushMethod)
admin.site.register(DataFeedPollInformation)
admin.site.register(DataFeedSubscriptionMethod)