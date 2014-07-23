# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from django.contrib import admin
import models

class ContentBindingSubtypeInline(admin.TabularInline):
    model = models.ContentBindingSubtype

class DataCollectionAdmin(admin.ModelAdmin):
    filter_vertical = ("supported_content", )
    #TODO: make checking 'accept all content' disable the supported content selector
    pass
    
class InboxServiceAdmin(admin.ModelAdmin):
    filter_vertical = ("supported_content", )
    #TODO: make checking 'accept all content' disable the supported content selector
    fieldsets = (
        (None, {
            'classes': ('wide', ),
            'fields': ('name', 'path', 'description', 'supported_message_bindings', 'supported_protocol_bindings', 'inbox_message_handler', 'enabled', 'accept_all_content', 'supported_content',)
        }),
        ('Destination Collection Options', {
            #'classes': ('collapse', ),
            'fields': ('destination_collection_status', 'destination_collections', )
        })
    )
    pass

class InboxMessageAdmin(admin.ModelAdmin):
    pass

class DiscoveryServiceAdmin(admin.ModelAdmin):
    pass

class PollServiceAdmin(admin.ModelAdmin):
    pass

class CollectionManagementServiceAdmin(admin.ModelAdmin):
    pass

class ProtocolBindingAdmin(admin.ModelAdmin):
    pass

class MessageBindingAdmin(admin.ModelAdmin):
    pass
    
class ContentBindingAdmin(admin.ModelAdmin):
    #list_display = ['name', 'description', 'id', 'binding_id', 'date_created', 'date_updated']
    inlines = [ContentBindingSubtypeInline]
    pass

#class ContentBindingSubtypeAdmin(admin.ModelAdmin):
#    #list_display = ['name', 'description', 'id', 'binding_id', 'date_created', 'date_updated']
#    pass

class ContentBlockAdmin(admin.ModelAdmin):
    pass

#class ContentBindingAndSubtypeAdmin(admin.ModelAdmin):
#    pass

class ServiceHandlerAdmin(admin.ModelAdmin):
    pass

class ValidatorAdmin(admin.ModelAdmin):
    pass

#class ResultSetAdmin(admin.ModelAdmin):
#    list_display = ['result_id', 'data_collection', 'begin_ts', 'end_ts']

def register_admins():
    """
    This function registers all the model admins. This isn't done by default.
    """
    admin.site.register(models.InboxService, InboxServiceAdmin)
    admin.site.register(models.DiscoveryService, DiscoveryServiceAdmin)
    admin.site.register(models.PollService, PollServiceAdmin)
    admin.site.register(models.CollectionManagementService, CollectionManagementServiceAdmin)
    admin.site.register(models.DataCollection, DataCollectionAdmin)
    admin.site.register(models.ContentBlock, ContentBlockAdmin)
    admin.site.register(models.MessageBinding, MessageBindingAdmin)
    admin.site.register(models.ContentBinding, ContentBindingAdmin)
    #admin.site.register(models.ContentBindingSubtype, ContentBindingSubtypeAdmin)
    admin.site.register(models.ProtocolBinding, ProtocolBindingAdmin)
    admin.site.register(models.ServiceHandler, ServiceHandlerAdmin)
    admin.site.register(models.Validator, ValidatorAdmin)
    admin.site.register(models.InboxMessage, InboxMessageAdmin)
    #admin.site.register(models.ContentBindingAndSubtype, ContentBindingAndSubtypeAdmin)
    #admin.site.register(ResultSet, ResultSetAdmin)
    #admin.site.register(DataCollectionPushMethod)
    #admin.site.register(DataCollectionPollInformation)
    #admin.site.register(DataCollectionSubscriptionMethod)