# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

from django.db import models
from django.contrib.auth.models import User
from dateutil.tz import tzutc
import datetime

MAX_ID_LEN      = 128
MAX_NAME_LEN    = 128

class ProtocolBindingId(models.Model):
    title = models.CharField(max_length=MAX_NAME_LEN, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_ID_LEN)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s' % (self.binding_id)

class ContentBindingId(models.Model):
    title = models.CharField(max_length=MAX_NAME_LEN, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_ID_LEN)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s' % (self.binding_id)

class MessageBindingId(models.Model):
    title = models.CharField(max_length=MAX_NAME_LEN, blank=True)
    description = models.TextField(blank=True)
    binding_id = models.CharField(max_length=MAX_ID_LEN)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        if self.title:
            return u'%s' % (self.title)
        else:
            return u'%s' % (self.binding_id)

class DataFeedPushMethod(models.Model):
    title = models.CharField(max_length=MAX_NAME_LEN, blank=True)
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
    
class DataFeedPollInformation(models.Model):
    title = models.CharField(max_length=MAX_NAME_LEN, blank=True)
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
    
class DataFeedSubscriptionMethod(models.Model):
    title = models.CharField(max_length=MAX_NAME_LEN, blank=True)
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
    
class DataFeed(models.Model):    
    name = models.CharField(max_length=MAX_NAME_LEN) # this will be used in the URL to access this feed
    description = models.TextField(blank=True)
    users = models.ManyToManyField(User) # users allowed to access this data feed.
    #authentication_required = models.BooleanField(default=True)
    
    supported_content_bindings = models.ManyToManyField(ContentBindingId)
    push_methods = models.ManyToManyField(DataFeedPushMethod)
    poll_service_instances = models.ManyToManyField(DataFeedPollInformation)
    subscription_methods = models.ManyToManyField(DataFeedSubscriptionMethod)
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.title)

    class Meta:
        ordering = ['name']

class ContentBlock(models.Model):
    title = models.CharField(max_length=MAX_NAME_LEN, blank=True) # not required by TAXII
    description = models.TextField(blank=True) # not required by TAXII
    
    data_feeds = models.ManyToManyField(DataFeed)
    timestamp_label = models.DateTimeField(default=lambda:datetime.datetime.now(tzutc())) # need to ensure uniqueness of this field
    submitted_by = models.ForeignKey(User, blank=True, null=True)#Not sure this is needed, but we track it anyway
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

class DataFeedSubscription(models.Model):
    subscription_id = models.CharField(max_length=128, unique=True) # uri formatted subscription id
    user = models.ForeignKey(User)
    data_feed = models.ForeignKey(DataFeed)
    data_feed_method = models.ForeignKey(DataFeedSubscriptionMethod)
    active = models.BooleanField(default=True)    
    expires = models.DateTimeField()
    
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    def __unicode__(self):
        return u'%s' % (self.title)

    class Meta:
        ordering = ['subscription_id']
