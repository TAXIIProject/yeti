# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import re
from django.contrib import admin
from taxii_services.models import Inbox, DataFeed, MessageBindingId, ContentBindingId, ContentBlock, ProtocolBindingId, DataFeedPushMethod, DataFeedPollInformation, DataFeedSubscriptionMethod
from taxii_services.forms import DataFeedModelForm, InboxModelForm

class DataFeedAdmin(admin.ModelAdmin):
    form = DataFeedModelForm
    list_display = ['name', 'description']
    
class InboxAdmin(admin.ModelAdmin):
    form = InboxModelForm    
    
class ProtocolBindingIdAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'id', 'binding_id', 'date_created', 'date_updated']

class MessageBindingIdAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'id', 'binding_id', 'date_created', 'date_updated']
    
class ContentBindingIdAdmin(admin.ModelAdmin):
    list_display = ['title', 'description', 'id', 'binding_id', 'date_created', 'date_updated']

class ContentBlockAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'description', 'timestamp_label','submitted_by', 'message_id', 'content_binding', 'content', 'padding', 'date_created', 'date_updated']

admin.site.register(Inbox, InboxAdmin)
admin.site.register(DataFeed, DataFeedAdmin)
admin.site.register(ContentBlock, ContentBlockAdmin)
admin.site.register(MessageBindingId, MessageBindingIdAdmin)
admin.site.register(ContentBindingId, ContentBindingIdAdmin)
admin.site.register(ProtocolBindingId, ProtocolBindingIdAdmin)
admin.site.register(DataFeedPushMethod)
admin.site.register(DataFeedPollInformation)
admin.site.register(DataFeedSubscriptionMethod)