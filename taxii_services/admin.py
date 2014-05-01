# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from django.contrib import admin
from taxii_services.models import Inbox, DataCollection, MessageBindingId, ContentBindingId, ContentBlock, ProtocolBindingId, DataCollectionPushMethod, DataCollectionPollInformation, DataCollectionSubscriptionMethod, ResultSet
from taxii_services.forms import DataCollectionModelForm, InboxModelForm

class DataCollectionAdmin(admin.ModelAdmin):
    form = DataCollectionModelForm
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

class ResultSetAdmin(admin.ModelAdmin):
    list_display = ['result_id', 'data_collection', 'begin_ts', 'end_ts']

admin.site.register(Inbox, InboxAdmin)
admin.site.register(DataCollection, DataCollectionAdmin)
admin.site.register(ContentBlock, ContentBlockAdmin)
admin.site.register(MessageBindingId, MessageBindingIdAdmin)
admin.site.register(ContentBindingId, ContentBindingIdAdmin)
admin.site.register(ProtocolBindingId, ProtocolBindingIdAdmin)
admin.site.register(ResultSet, ResultSetAdmin)
admin.site.register(DataCollectionPushMethod)
admin.site.register(DataCollectionPollInformation)
admin.site.register(DataCollectionSubscriptionMethod)

