# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

from django.db import models
from django.contrib.auth.models import User
from dateutil.tz import tzutc
import datetime

class ProtocolBindingId(models.Model):
    binding_id = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.binding_id)

class ContentBindingId(models.Model):
    binding_id = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s' % (self.binding_id)

class MessageBindingId(models.Model):
    binding_id = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s' % (self.binding_id)

class DataFeedPushMethods(models.Model):
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_binding = models.ForeignKey(MessageBindingId)
    
class DataFeedPollInformation(models.Model):
    address = models.URLField()
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_bindings = models.ManyToManyField(MessageBindingId)
    
    class Meta:
        ordering = ['address']
    
class DataFeedSubscriptionMethod(models.Model):
    address = models.URLField()
    protocol_binding = models.ForeignKey(ProtocolBindingId)
    message_bindings = models.ManyToManyField(MessageBindingId)
    
    class Meta:
        ordering = ['address']
    
class DataFeed(models.Model):    
    name = models.CharField(max_length=128)
    description = models.TextField()
    users = models.ManyToManyField(User) # users allowed to access this data feed.
    
    supported_content_bindings = models.ManyToManyField(ContentBindingId)
    push_methods = models.ManyToManyField(DataFeedPushMethods)
    poll_service_instances = models.ManyToManyField(DataFeedPollInformation)
    subscription_methods = models.ManyToManyField(DataFeedSubscriptionMethod)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.name)

    class Meta:
        ordering = ['name']

class ContentBlock(models.Model):
    # QUESTIONS:
    # + Do we want to record message ids associated with content blocks?
    
    data_feed = models.ManyToManyField(DataFeed)
    timestamp_label = models.DateTimeField(default=lambda:datetime.datetime.now(tzutc()))
    submitted_by = models.ForeignKey(User)#Not sure this is needed, but we track it anyway
    
    #TAXII Properties of a content block
    content_binding = models.ForeignKey(ContentBindingId)
    content = models.TextField()
    padding = models.TextField()
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.id)

    class Meta:
        ordering = ['timestamp_label']

class DataFeedSubscription(models.Model):
    subscription_id = models.CharField(max_length=256, unique=True) # uri formatted subscription id
    user = models.ForeignKey(User)
    data_feed = models.ForeignKey(DataFeed)
    data_feed_method = models.ForeignKey(DataFeedSubscriptionMethod)
    active = models.BooleanField(default=True)    
    expires = models.DateTimeField()
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.name)

