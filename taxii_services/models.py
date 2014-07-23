# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from django.db import models
from django.db.models.signals import post_save

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

import libtaxii.messages_11 as tm11

MAX_NAME_LENGTH = 256

#A number of choice tuples are defined here. In all cases the choices are:
# (database_value, display_value). Where possible, database_value is 
# a constant from libtaxii.messages_11. There is one handler per TAXII
# message exchange


INBOX_MESSAGE_HANDLER = (tm11.MSG_INBOX_MESSAGE, 'Inbox Service - Inbox Message Handler')
POLL_REQUEST_HANDLER = (tm11.MSG_POLL_REQUEST, 'Poll Service - Poll Request Handler')
POLL_FULFILLMENT_REQUEST_HANDLER = (tm11.MSG_POLL_FULFILLMENT_REQUEST , 'Poll Service - Poll Fu;fillment Request Handler')
DISCOVERY_REQUEST_HANDLER = (tm11.MSG_DISCOVERY_REQUEST, 'Discovery Service - Discovery Request Handler')
COLLECTION_INFORMATION_REQUEST_HANDLER = (tm11.MSG_COLLECTION_INFORMATION_REQUEST, 'Collection Management Service - Collection Information Handler')
SUBSCRIPTION_MANAGEMENT_REQUEST_HANDLER = (tm11.MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST , 'Collection Management Service - Subscription Management Handler')
OTHER_HANDLER = ('other', 'Other Request Handler')

MESSAGE_HANDLER_CHOICES = (INBOX_MESSAGE_HANDLER, POLL_REQUEST_HANDLER, POLL_FULFILLMENT_REQUEST_HANDLER, 
                DISCOVERY_REQUEST_HANDLER, COLLECTION_INFORMATION_REQUEST_HANDLER, 
                SUBSCRIPTION_MANAGEMENT_REQUEST_HANDLER, OTHER_HANDLER)

ACTIVE_STATUS = (tm11.SS_ACTIVE, 'Active')
PAUSED_STATUS = (tm11.SS_PAUSED, 'Paused')
UNSUBSCRIBED_STATUS = (tm11.SS_UNSUBSCRIBED, 'Unsibscribed')

SUBSCRIPTION_STATUS_CHOICES = (ACTIVE_STATUS, PAUSED_STATUS, UNSUBSCRIBED_STATUS)

FULL_RESPONSE = (tm11.RT_FULL, 'Full')
COUNT_RESPONSE = (tm11.RT_COUNT_ONLY, 'Count Only')

RESPONSE_CHOICES = (FULL_RESPONSE, COUNT_RESPONSE)

DATA_FEED = (tm11.CT_DATA_FEED, 'Data Feed')
DATA_SET = (tm11.CT_DATA_SET, 'Data Set')

DATA_COLLECTION_CHOICES = (DATA_FEED, DATA_SET)

REQUIRED = ('REQUIRED', 'required')
OPTIONAL = ('OPTIONAL', 'optional')
PROHIBITED = ('PROHIBITED', 'prohibited')

ROP_CHOICES = (REQUIRED, OPTIONAL, PROHIBITED)

#TODO: probably "unique=True" could be used at least once in each model. should try to figure out where it makes sense.

class Validator(models.Model):
    """
    """
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    description = models.TextField(blank=True)
    validator = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.validator)
    
    class Meta:
        ordering = ['name']

class ContentBinding(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    validator = models.ForeignKey(Validator, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.name:
            return u'%s' % (self.name)
        else:
            return u'%s' % (self.binding_id)
        
    class Meta:
        verbose_name = "Content Binding"

class ContentBindingSubtype(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(ContentBinding)
    subtype_id = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    validator = models.ForeignKey(Validator, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        if self.name:
            return u'%s' % (self.name)
        else:
            return u'%s' % (self.subtype_id)
        
    class Meta:
        verbose_name = "Content Binding Subtype"

class ContentBindingAndSubtype(models.Model):
    content_binding = models.ForeignKey(ContentBinding)
    subtype = models.ForeignKey(ContentBindingSubtype, blank=True, null=True)
    #TODO: Add an enabled/disabled button
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        #uni = "%s (%s) > " % (self.content_binding.name, self.content_binding.binding_id)
        uni = "%s > " % self.content_binding.name
        if self.subtype:
            #uni += "%s (%s)" % (self.subtype.name, self.subtype.subtype_id)
            uni += "%s" % self.subtype.name
        else:
            uni += "(All)"
        
        return uni
    
    class Meta:
        verbose_name = "Content Binding And Subtype"
        unique_together = ('content_binding', 'subtype',)

def update_content_binding(sender, **kwargs):
    if not kwargs['created']:
        return
    
    cbas = ContentBindingAndSubtype(content_binding = kwargs['instance'], subtype=None)
    cbas.save()

def update_content_binding_subtype(sender, **kwargs):
    if not kwargs['created']:
        return
    subtype = kwargs['instance']
    cbas = ContentBindingAndSubtype(content_binding = subtype.parent, subtype = subtype)
    cbas.save()

post_save.connect(update_content_binding, sender=ContentBinding)
post_save.connect(update_content_binding_subtype, sender=ContentBindingSubtype)
#Post delete handlers don't need to be written because they are part of how foreign keys work

class RecordCount(models.Model):
    record_count = models.IntegerField()
    partial_count = models.BooleanField(default=False)

class SubscriptionInformation(models.Model):
    collection_name = models.CharField(max_length=MAX_NAME_LENGTH)
    subscription_id = models.CharField(max_length=MAX_NAME_LENGTH)#TODO: Index on this
    exclusive_begin_timestamp_label = models.DateTimeField(blank=True, null=True)
    inclusive_end_timestamp_label = models.DateTimeField(blank=True, null=True)

class MessageBinding(models.Model):
    """
    Represents a Message Binding, used to establish the supported syntax
    for a given TAXII exchange, "e.g., XML".
    
    Ex:
    XML message binding id : "urn:taxii.mitre.org:message:xml:1.1"
    """
    name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.name:
            return u'%s' % (self.name)
        else:
            return u'%s' % (self.binding_id)

    class Meta:
        verbose_name = "Message Binding"

class ProtocolBinding(models.Model):
    """
    Represents a Protocol Binding, used to establish the supported transport
    for a given TAXII exchange, "e.g., HTTP".
    
    Ex:
    HTTP Protocol Binding : "urn:taxii.mitre.org:protocol:http:1.0"
    """
    name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.name:
            return u'%s' % (self.name)
        else:
            return u'%s' % (self.binding_id)

    class Meta:
        verbose_name = "Protocol Binding"

# class PushMethod(models.Model):
    # """
    # Used to establish the protocols that can be used to push content via
    # a subscription. This appears in a Collection Information Response message,
    # as defined by the TAXII Services Specification.
    # """
    # name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True)
    # description = models.TextField(blank=True)
    # protocol_binding = models.ForeignKey(ProtocolBinding)
    # message_bindings = models.ManyToManyField(MessageBinding)
    
    # date_created = models.DateTimeField(auto_now_add=True)
    # date_updated = models.DateTimeField(auto_now=True)
    
    # def __unicode__(self):
        # if self.name:
            # return u'%s' % (self.name)
        # else:
            # return u'%s | %s' % (self.protocol_binding, self.message_binding)
    
    # class Meta:
        # verbose_name = "Data Collection Push Method"

# class PollInformation(models.Model):
    # """
    # Used to establish the supported protocols and address of a Data Collection.
    # This appears in a Collection Information Response message, as defined by the
    # TAXII Services Specification.
    # """
    # name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True)
    # description = models.TextField(blank=True)
    # address = models.URLField()
    # protocol_binding = models.ForeignKey(ProtocolBinding)
    # message_bindings = models.ManyToManyField(MessageBinding)
    
    # date_created = models.DateTimeField(auto_now_add=True)
    # date_updated = models.DateTimeField(auto_now=True)
    
    # def __unicode__(self):
        # if self.name:
            # return u'%s' % (self.name)
        # else:
            # return u'%s | %s' % (self.protocol_binding, self.message_binding)
    
    # class Meta:
        # ordering = ['address']
        # verbose_name = "Data Collection Poll Information"
        # verbose_name_plural = "Data Collection Poll Information"
    
# class SubscriptionMethod(models.Model):
    # """
    # Used to identify the protocol and address of the TAXII daemon hosting
    # the Collection Management Service that can process subscriptions for a TAXII
    # Data Collection. This appears in a Collection Information Response message, as defined
    # by the TAXII Services Specification.
    # """
    # name = models.CharField(max_length=MAX_NAME_LENGTH, blank=True)
    # description = models.TextField(blank=True)
    # address = models.URLField()
    # protocol_binding = models.ForeignKey(ProtocolBinding)
    # message_bindings = models.ManyToManyField(MessageBinding)
    
    # date_created = models.DateTimeField(auto_now_add=True)
    # date_updated = models.DateTimeField(auto_now=True)
    
    # def __unicode__(self):
        # if self.name:
            # return u'%s' % (self.name)
        # else:
            # return u'%s | %s' % (self.protocol_binding, self.message_binding)
    
    # class Meta:
        # ordering = ['address']  
        # verbose_name = "Data Collection Subscription Method"

class DataCollection(models.Model):
    name = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    description = models.TextField(blank=True)
    type = models.CharField(max_length=MAX_NAME_LENGTH, choices=DATA_COLLECTION_CHOICES)#Choice - Data Feed or Data Set
    accept_all_content = models.BooleanField(default=False)
    supported_content = models.ManyToManyField(ContentBindingAndSubtype, blank=True, null=True)
    content_blocks = models.ManyToManyField('ContentBlock', blank=True, null=True)
    
    #TODO: Does query info go here?
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        ordering = ['name']
        verbose_name = "Data Collection"

class ServiceHandler(models.Model):
    """
    """
    
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    description = models.TextField(blank=True)
    handler = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    type = models.CharField(max_length=MAX_NAME_LENGTH, choices = MESSAGE_HANDLER_CHOICES)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s (%s)' % (self.name, self.handler)
    
    class Meta:
        ordering = ['name']

class _TaxiiService(models.Model):
    """
    Not to be used by users directly. Defines common fields that all 
    TAXII Services use
    """
    
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    path = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    description = models.TextField(blank=True)
    supported_message_bindings = models.ManyToManyField(MessageBinding)
    supported_protocol_bindings = models.ManyToManyField(ProtocolBinding)
    enabled = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % self.name
    
    class Meta:
        ordering = ['name']
        

class InboxService(_TaxiiService):
    inbox_message_handler = models.ForeignKey(ServiceHandler, limit_choices_to={'type__in': [tm11.MSG_INBOX_MESSAGE, 'other']})
    destination_collection_status = models.CharField(max_length=MAX_NAME_LENGTH, choices=ROP_CHOICES)
    destination_collections = models.ManyToManyField(DataCollection, blank=True)
    accept_all_content = models.BooleanField(default=False)
    supported_content = models.ManyToManyField(ContentBindingAndSubtype, blank=True, null=True)
    
    #TODO: Whast does it mean when the inbox supports a content binding that it's underlying data collections dont?
    #TODO: How to handle subtypes?
    #TODO: How does destination_collections impact which
    #      Content Bindings are supported?
    
    #TODO: Does this do what I want, or do I need to 
    # do something like self.meta.verbose_name = 'dsa' ?
    #class Meta:
    #    verbose_name = "Inbox Service"
    #    verbose_name_plural = "Inbox Services"


class InboxMessage(models.Model):
    """
    Used to store information about received Inbox Messages
    """
    #TODO: What should I index on?
    #TODO: NONE of these fields should be editable in the admin
    message_id = models.CharField(max_length=MAX_NAME_LENGTH)
    sending_ip = models.CharField(max_length=MAX_NAME_LENGTH)
    datetime_received = models.DateTimeField(auto_now_add=True)
    result_id = models.CharField(max_length=MAX_NAME_LENGTH, blank=True, null=True)
    record_count = models.ForeignKey(RecordCount, blank=True, null=True)
    subscription_information = models.ForeignKey(SubscriptionInformation, blank=True, null=True)
    received_via = models.ForeignKey(InboxService, blank=True, null=True)
    original_message = models.TextField(blank=True, null=True)
    content_block_count = models.IntegerField()
    content_blocks_saved = models.IntegerField()
    
    def __unicode__(self):
        return u'%s - %s' % (self.message_id, self.datetime_received)
    
    class Meta:
        ordering = ['datetime_received']

class ContentBlock(models.Model):
    description = models.TextField(blank=True) # not required by TAXII
    
    timestamp_label = models.DateTimeField(auto_now_add=True)
    inbox_message = models.ForeignKey(InboxMessage, blank=True, null=True)
    
    #TAXII Properties of a content block
    content_binding_and_subtype = models.ForeignKey(ContentBindingAndSubtype)
    content = models.TextField()
    padding = models.TextField(blank=True)
    
    date_created = models.DateTimeField(auto_now_add=True) # look at this for problems with apache instances
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.id)

    class Meta:
        ordering = ['timestamp_label']
        verbose_name = "Content Block"

class PollService(_TaxiiService):
    poll_request_handler = models.ForeignKey(ServiceHandler, related_name='poll_request', limit_choices_to={'type__in': [tm11.MSG_POLL_REQUEST, 'other']})
    poll_fulfillment_handler = models.ForeignKey(ServiceHandler, related_name='poll_fulfillment', limit_choices_to={'type__in': [tm11.MSG_POLL_FULFILLMENT_REQUEST, 'other']}, blank=True, null=True)
    data_collections = models.ManyToManyField(DataCollection)


class CollectionManagementService(_TaxiiService):
    collection_information_handler = models.ForeignKey(ServiceHandler, related_name='collection_information', limit_choices_to={'type__in': [tm11.MSG_COLLECTION_INFORMATION_REQUEST, 'other']}, blank=True, null=True)
    subscription_management_handler = models.ForeignKey(ServiceHandler, related_name='subscription_management', limit_choices_to={'type__in': [tm11.MSG_MANAGE_COLLECTION_SUBSCRIPTION_REQUEST, 'other']}, blank=True, null=True)
    advertised_collections = models.ManyToManyField(DataCollection, blank=True, null=True)#TODO: This field is also used to determine which Collections this service processes subscriptions for. Is that right?
    #TODO: Add a validation step to make sure at least one of subscription management or collection_information handler is selected.

class DiscoveryService(_TaxiiService):
    discovery_handler = models.ForeignKey(ServiceHandler, limit_choices_to={'type__in': [tm11.MSG_DISCOVERY_REQUEST, 'other']})
    advertised_discovery_services = models.ManyToManyField('self', blank=True)
    advertised_inbox_services = models.ManyToManyField(InboxService, blank=True)
    advertised_poll_services = models.ManyToManyField(PollService, blank=True)
    advertised_collection_management_services = models.ManyToManyField(CollectionManagementService, blank=True)

#TODO: Something using GenericForeignKey could be used to create a service registry    
#class ServiceRegistry(models.Model):
#    content_type = models.ForeignKey(ContentType)
#    object_id = models.PositiveIntegerField()
#    content_object = generic.GenericForeignKey('content_type', 'object_id')

class Subscription(models.Model):
    subscription_id = models.CharField(max_length=MAX_NAME_LENGTH, unique=True)
    response_type = models.CharField(max_length=MAX_NAME_LENGTH, choices = RESPONSE_CHOICES, default=tm11.RT_FULL)
    content_binding_and_subtype = models.ManyToManyField(ContentBindingAndSubtype, blank=True, null=True)
    query = models.TextField(blank=True)
    #push_parameters = models.ForeignKey(PushParameters)#TODO: Create a push parameters object
    status = models.CharField(max_length=MAX_NAME_LENGTH, choices = SUBSCRIPTION_STATUS_CHOICES, default=tm11.SS_ACTIVE)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

