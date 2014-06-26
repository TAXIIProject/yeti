# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

from django.db import models
from dateutil.tz import tzutc
import datetime

MAX_ID_LEN      = 128 
MAX_TITLE_LEN   = 128

class ProtocolBindingId(models.Model):
    """
    Represents a protocol binding id, used to establish the exchange protocol
    supported by a TAXII implementation.
    
    Ex: 
    HTTP protocol binding id : "urn:taxii.mitre.org:protocol:http:1.0"
    HTTPS protocol binding id : "urn:taxii.mitre.org:protocol:https:1.0"
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_ID_LEN)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s' % (self.binding_id)

    class Meta:
        verbose_name = "Protocol Binding Id"

class ContentBindingId(models.Model):
    """
    Represents a content binding id, used to establish the supported content
    types for a given TAXII exchange (e.g., Poll, Inbox, etc.).
    
    Ex:
    STIX v1.0 content binding id : "urn:stix.mitre.org:xml:1.1"
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_ID_LEN)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s' % (self.binding_id)
        
    class Meta:
        verbose_name = "Content Binding Id"

class MessageBindingId(models.Model):
    """
    Represents a message binding id, used to establish the supported syntax
    for a given TAXII exchange, "e.g., XML".
    
    Ex:
    XML message binding id : "urn:taxii.mitre.org:message:xml:1.0"
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_ID_LEN)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s' % (self.binding_id)

    class Meta:
        verbose_name = "Message Binding Id"

class DataCollectionPushMethod(models.Model):
    """
    Used to establish the protocols that can be used to push content via
    a subscription. This appears in a Collection Information Response message,
    as defined by the TAXII Services Specification.
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_binding = models.ForeignKey(MessageBindingId)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s | %s' % (self.protocol_binding, self.message_binding)
    
    class Meta:
        verbose_name = "Data Collection Push Method"
    
class DataCollectionPollInformation(models.Model):
    """
    Used to establish the supported protocols and address of a Data Collection.
    This appears in a Collection Information Response message, as defined by the
    TAXII Services Specification.
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    address = models.URLField()
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_bindings = models.ManyToManyField(MessageBindingId)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s | %s' % (self.protocol_binding, self.message_binding)
    
    class Meta:
        ordering = ['address']
        verbose_name = "Data Collection Poll Information"
        verbose_name_plural = "Data Collection Poll Information"
    
class DataCollectionSubscriptionMethod(models.Model):
    """
    Used to identify the protocol and address of the TAXII daemon hosting
    the Collection Management Service that can process subscriptions for a TAXII
    Data Collection. This appears in a Collection Information Response message, as defined
    by the TAXII Services Specification.
    """
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True)
    description = models.TextField(blank=True)
    address = models.URLField()
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_bindings = models.ManyToManyField(MessageBindingId)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s | %s' % (self.protocol_binding, self.message_binding)
    
    class Meta:
        ordering = ['address']  
        verbose_name = "Data Collection Subscription Method"

class ContentBlock(models.Model):
    """Represents the content block of a TAXII Poll Response or Inbox message."""
    title = models.CharField(max_length=MAX_TITLE_LEN, blank=True) # not required by TAXII
    description = models.TextField(blank=True) # not required by TAXII
    
    timestamp_label = models.DateTimeField(default=lambda:datetime.datetime.now(tzutc())) # need to ensure uniqueness of this field
    submitted_by = models.CharField(max_length=25, blank=True, null=True) # This should track IP addresses
    message_id = models.CharField(max_length=MAX_ID_LEN, blank=True) # associated message id if present. is there always a 1-to-1 for message ids and content blocks
    
    #TAXII Properties of a content block
    content_binding = models.ForeignKey(ContentBindingId)
    content = models.TextField()
    padding = models.TextField(blank=True)
    
    date_created = models.DateTimeField(auto_now_add=True) # look at this for problems with apache instances
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.id)

    class Meta:
        ordering = ['timestamp_label']
        verbose_name = "Content Block"
    
class DataCollection(models.Model):
    """Represents a TAXII Data Collection"""   
    name = models.CharField(max_length=MAX_TITLE_LEN) # this will be used to access this data collection
    description = models.TextField(blank=True)
    supported_content_bindings = models.ManyToManyField(ContentBindingId)
    push_methods = models.ManyToManyField(DataCollectionPushMethod)
    poll_service_instances = models.ManyToManyField(DataCollectionPollInformation)
    subscription_methods = models.ManyToManyField(DataCollectionSubscriptionMethod, blank=True, null=True)
    content_blocks = models.ManyToManyField(ContentBlock, blank=True, null=True)
    queryable = models.BooleanField(default=False)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        ordering = ['name']
        verbose_name = "Data Collection"

class DataCollectionSubscription(models.Model):
    """Represents a Data Collection Subscription. This is not used by YETI at the moment."""
    subscription_id = models.CharField(max_length=MAX_ID_LEN, unique=True) # uri formatted subscription id
    data_collection = models.ForeignKey(DataCollection)
    data_collection_method = models.ForeignKey(DataCollectionSubscriptionMethod)
    active = models.BooleanField(default=True)    
    expires = models.DateTimeField()
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.title)

    class Meta:
        ordering = ['subscription_id']
        verbose_name = "Data Collection Subscription"
        
class Inbox(models.Model):
    """
    Characterizes a TAXII Inbox. Inboxes are the mechanism by which TAXII consumers
    receive data from TAXII publishers. This Inbox implementation allows an Inbox
    to be "bound" to zero or more Data Collections, meaning that data received by an Inbox
    can populate Data Collections if it is configured it as such.
    """
    name = models.CharField(max_length=MAX_TITLE_LEN, unique=True) # this will become part of the URL where it can be accessed at
    description = models.TextField(blank=True)
    supported_content_bindings = models.ManyToManyField(ContentBindingId)
    supported_message_bindings = models.ManyToManyField(MessageBindingId)
    content_blocks = models.ManyToManyField(ContentBlock, blank=True, null=True) # content blocks associated with this inbox
    supported_protocol_binding = models.ForeignKey(ProtocolBindingId)
    data_collections = models.ManyToManyField(DataCollection, blank=True, null=True) # data received at an inbox will automatically be made available on these data collections
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % self.name
    
    class Meta:
        ordering = ['name']
        verbose_name = "Inbox"
        verbose_name_plural = "Inboxes"
        
class ResultSet(models.Model):
    """
    Contains a result set for asynchronous polling.
    """
    data_collection = models.ForeignKey(DataCollection)
    result_id = models.TextField(unique=True)
    content_blocks = models.ManyToManyField(ContentBlock, blank=True, null=True)#Can have 0 Content Blocks
    begin_ts = models.DateTimeField(blank=True, null=True)
    end_ts = models.DateTimeField(blank=True, null=True)
    
    def __unicode__(self):
        return u'%s' % self.result_id
    
    #def count_blocks(self, obj):
    #    return 'dsa'#len(self.content_blocks)
    #
    #count_blocks.short_description = 'Content Blocks (count)'
    
    class Meta:
        ordering = ['result_id']
        verbose_name = 'ResultSet'
        verbose_name_plural = 'ResultSets'

