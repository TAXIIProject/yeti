# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import models
from django.http import Http404
from itertools import chain
import libtaxii as t
import libtaxii.messages_11 as tm11
import libtaxii.taxii_default_query as tdq
import datetime
from dateutil.tz import tzutc
from importlib import import_module

def get_service_from_path(path):
    #TODO: Can this code be cleaned up a bit?
    #TODO: Probably the paths should be unique across all services
    # right now you could have two different services with the same 
    # path and the code search order would determine which
    # one gets returned
    
    #Thought: Have a path object that must be unique and 
    # the path object can only have one outbound relationship?
    try:
        return models.InboxService.objects.get(path = path, enabled=True)
    except:
        pass
    
    try:
        return models.DiscoveryService.objects.get(path = path, enabled=True)
    except:
        pass
    
    try:
        return models.PollService.objects.get(path = path, enabled=True)
    except:
        pass
    
    try:
        return models.CollectionManagementService.objects.get(path = path, enabled=True)
    except:
        pass
    
    raise Http404("No TAXII service at specified path")

def get_service_handler(service, taxii_message):
    if isinstance(service, models.InboxService):
        if isinstance(taxii_message, tm11.InboxMessage):
            handler_string = service.inbox_message_handler.handler
        else:
            raise Exception("message type not supported")#TODO: Better error
    elif isinstance(service, models.PollService):
        if isinstance(taxii_message, tm11.PollRequest):
            handler_string = service.poll_request_handler.handler
        elif isinstance(taxii_message, tm11.PollFulfillmentRequest):
            handler_string = service.poll_fulfillment_handler.handler
        else:
            raise Exception("message type not supported")#TODO: Better error
    elif isinstance(service, models.DiscoveryService):
        if isinstance(taxii_message, tm11.DiscoveryRequest):
            handler_string = service.discovery_handler.handler
        else:
            raise Exception("message type not supported")#TODO: Better error
    elif isinstance(service, models.CollectionManagementService):
        if isinstance(taxii_message, tm11.CollectionInformationRequest):
            handler_string = service.collection_information_handler.handler
        elif isinstance(taxii_message, tm11.SubscriptionManagementRequest):
            handler_string = service.subscription_management_handler.handler
        else:
            raise Exception("message type not supported")#TODO: Better error
    else:
        raise Exception("This shouldn't happen!")
    
    module_name, method_name = handler_string.rsplit('.', 1)
    module = import_module(module_name)
    handler = getattr(module, method_name)
    
    return handler

def get_push_methods(data_collection):
    #TODO: Implement this
    return None

#TODO: This is a model -> TAXII 1.1 specific thing. Should it be marked as such, named as such, labeled as such?
#      Not sure how this should be segmented out or whatever. Maybe also take an argument that's the message binding id to provide
#      the right output format?
def get_polling_service_instances(data_collection):
    poll_instances = []
    poll_services = models.PollService.all.filter(data_collections=data_collection)
    for poll_service in poll_services:
        message_bindings = [mb.binding_id for mb in poll_service.supported_message_bindings.all()]
        for supported_protocol_binding in poll_service.supported_protocol_bindings.all():
            poll_instance = tm11.PollingServiceInstance(supported_protocol_binding.binding_id, poll_service.path, message_bindings)
            poll_instances.append(poll_instance)
    
    return poll_instances

def get_subscription_methods(data_collection):
    #TODO: Probably wrong, but here's the idea
    subscription_methods = []
    collection_management_services = models.CollectionManagementService.all.filter(advertised_collections=data_collection)
    for collection_management_service in collection_management_services:
        message_bindings = [mb.binding_id for mb in collection_management_service.supported_message_bindings.all()]
        for supported_protocol_binding in collection_management_service.supported_protocol_bindings.all():
            subscription_method = tm11.SubscriptionMethod(supported_protocol_binding.binding_id, collection_management_service.path, message_bindings)
            subscription_methods.append(subscription_method)
    
    return subscription_methods

def get_receiving_inbox_services(data_collection):
    receiving_inbox_services = []
    inbox_services = models.InboxService.all.filter(destination_collections=data_collection)
    for inbox_service in inbox_services:
        message_bindings = [mb.binding_id for mb in inbox_service.supported_message_bindings.all()]
        for supported_protocol_binding in inbox_service.supported_protocol_bindings.all():
            receiving_inbox_service = tm11.ReceivingInboxService(supported_protocol_binding.binding_id, inbox_service.path, message_bindings, supported_contents=None)#TODO: Work on supported_contents
            receiving_inbox_services.append(subscription_method)
    
    return receiving_inbox_services

def add_content_block_to_collection(content_block, collection):
    #If the content block has a binding id only
    # 1) accept if it there is a matching binding id + no subtype
    #If the content block has a binding id and subtype 
    # 2) accept it if there is a matching binding id + no subtype
    # 3) accept it if there is a matching binding id + subtype
    
    #Look up the content binding in the database
    try:
        binding = models.ContentBinding.get(binding_id=content_block.content_binding.binding_id)
    except:
        return False, 'Content Binding not located in database'
    
    #Try to match on content binding only - this satisfies conditions #1 & 2
    if len(collection.supported_content.filter(content_binding=binding, subtype=None)) > 0:
        collection.content_blocks.add(content_block)
    return True, None
    
    if len(content_block.content_binding.subtype_ids) == 0:
        return False, 'No match found for supplied content binding'
    
    #Look up the subtype ID in the database
    try:
        subtype = models.ContentBindingSubtype.get(subtype_id = content_block.content_binding.subtype_ids[0])
    except:
        return False, 'Content Binding Subtype not located in database'
    
    if len(collection.supported_content.filter(content_binding=binding, subtype=subtype)):
        collection.content_blocks.add(content_block)
        return True, None
    
    return False, 'No match could be found'

def is_content_supported(obj, content_block): #binding_id, subtype_id = None):
    """
    Takes an object and a content block and determines whether
    obj (usually an Inbox Service or Data Collection) supports that (
    e.g., whether the content block can be added).
    
    Decision process is:
    1. If obj accepts any content, return True
    2. If obj supports binding ID > (All), return True
    3. If obj supports binding ID and subtype ID, return True
    4. Otherwise, return False,
    
    Works on any model with 'accept_all_content' (bool) and 
    'supported_content' (many to many to ContentBindingAndSubtype) fields
    """
    
    binding_id = content_block.content_binding.binding_id
    subtype_id = None
    if len(content_block.content_binding.subtype_ids) > 0:
        subtype_id = content_block.content_binding.subtype_ids[0]
    
    #TODO: I think this works, but this logic can probably be cleaned up
    if obj.accept_all_content:
        print 'accepts all content'
        return True
    
    try:
        binding = models.ContentBinding.objects.get(binding_id = binding_id)
    except:
        raise
        return False
    
    if len(obj.supported_content.filter(content_binding = binding, subtype = None)) > 0:
        return True
    
    if not subtype_id:#No further checking can be done 
        print 'no further checking can be done'
        return False
    
    try:
        subtype = models.ContentBindingSubtype.objects.get(parent = binding, subtype_id = subtype_id)
    except:
        raise
        False
    
    if len(obj.supported_content.filter(content_binding = binding, subtype = subtype)) > 0:
        return True
    
    print 'all out of options!'
    return False
    

def get_supported_content(obj):
    """
    Works on any model with 'accept_any_content' (bool) and 
    'supported_content' (many to many to ContentBindingAndSubtype) fields
    """
    if obj.accept_all_content:
        return None#Indicates accept all
    
    supported_content = {}
    
    for content in obj.supported_content.all():
        binding_id = content.content_binding.binding_id
        subtype = content.subtype
        if binding_id not in supported_content:
            supported_content[binding_id] = tm11.ContentBinding(binding_id = binding_id)
        
        if subtype and subtype.subtype_id not in supported_content[binding_id].subtype_ids:
            supported_content[binding_id].subtype_ids.append(subtype.subtype_id)
    #TODO: If no content is supported, this will incorectly indicate that all content is supported
    return supported_content.values()


def get_supported_queries(poll_service):
    return None#TODO: Implement this

def discovery_handler(discovery_service, discovery_request, django_request):
    
    #Get all the enabled services that this discovery service advertises
    advertised_services = list(chain(discovery_service.advertised_discovery_services.filter(enabled=True),
                                     discovery_service.advertised_poll_services.filter(enabled=True),
                                     discovery_service.advertised_inbox_services.filter(enabled=True),
                                     discovery_service.advertised_collection_management_services.filter(enabled=True)))
    
    discovery_response = tm11.DiscoveryResponse(tm11.generate_message_id(), discovery_request.message_id)
    
    #Create a service instance for each advertised service
    #If a service supports multiple protocols, it has to be split into
    #one service instance for each protocol
    for service in advertised_services:
        st = None#Service_type
        sq = None#supported_query
        isac = None#inbox_service_accepted_content
        if isinstance(service, models.DiscoveryService):
            st = tm11.SVC_DISCOVERY
        elif isinstance(service, models.PollService):
            st = tm11.SVC_POLL
            sq = get_supported_queries(service)
        elif isinstance(service, models.InboxService):
            st = tm11.SVC_INBOX
            isac = get_supported_content(service)
        elif isinstance(service, models.CollectionManagementService):
            st = tm11.SVC_COLLECTION_MANAGEMENT
        else:#TODO: use a better exception
            raise Exception("Unknown service class %s" % service.__class__.__name__)
        
        for pb in service.supported_protocol_bindings.all():            
            si = tm11.ServiceInstance(
                         service_type = st,
                         services_version = t.VID_TAXII_SERVICES_11,
                         available = True,
                         protocol_binding = pb.binding_id,
                         service_address = service.path,#TODO: Get the server's real path and prepend it here
                         message_bindings = [mb.binding_id for mb in service.supported_message_bindings.all()],
                         supported_query = sq,
                         inbox_service_accepted_content = isac,
                         message = service.description
                         )
            discovery_response.service_instances.append(si)
    
    return discovery_response

def inbox_message_handler(inbox_service, inbox_message, django_request):
    
    num_dcns = len(inbox_message.destination_collection_names)
    
    if inbox_service.destination_collection_status == 'required' and num_dcns == 0:
        sm = tm11.StatusMessage(tm11.generate_message_id(), in_response_to=inbox_message.message_id, status_type=tm11.ST_DESTINATION_COLLECTION_ERROR)
        sm.message = 'A Destination_Collection_Name is required and none were specified'
        sm.status_detail = get_inbox_acceptable_destinations(inbox_service)
        return sm
    
    if inbox_service.destination_collection_status == 'prohibited' and num_dcns > 0:
        sm = tm11.StatusMessage(tm11.generate_message_id(), in_response_to=inbox_message.message_id, status_type=tm11.ST_DESTINATION_COLLECTION_ERROR)
        sm.message = 'Destination_Collection_Names are prohibited'
        return sm
    
    #Try to find all specified collection names
    collections = []
    for collection_name in inbox_message.destination_collection_names:
        try:
            collections.append(inbox_service.destination_collections.get(name=collection_name))
        except:
            raise
            sm = tm11.StatusMessage(tm11.generate_message_id(), in_response_to=inbox_message.message_id, status_type=tm11.ST_NOT_FOUND)
            sm.message = 'Invalid destination collection name'
            #TODO: Verify that this status_detail is being set right. Its probably not. should probably use a constant for ITEM.
            sm.status_detail = {'ITEM': collection_name}
            return sm
    
    #Save InboxMessage info to the database
    inbox_message_db = models.InboxMessage()#The database instance of the inbox message
    inbox_message_db.message_id = inbox_message.message_id
    inbox_message_db.sending_ip = django_request.META.get('REMOTE_ADDR', None)
    if inbox_message.result_id:
        inbox_message_db.result_id = inbox_message.result_id
    if inbox_message.record_count:
        rc = models.RecordCount()
        rc.record_count = inbox_message.record_count.record_count
        if inbox_message.record_count.partial_count:
            rc.partial_count = inbox_message.record_count.partial_count
        rc.save()
        inbox_message_db.record_count = rc
    
    if inbox_message.subscription_information:
        si = models.SubscriptionInformation()
        si.collection_name = inbox_message.subscription_information.collection_name
        si.subscription_id = inbox_message.subscription_information.subscription_id
        #TODO: These are probably wrong
        if inbox_message.subscription_information.exclusive_begin_timestamp_label:
            si.exclusive_begin_timestamp_label = inbox_message.subscription_information.exclusive_begin_timestamp_label
        if inbox_message.subscription_information.inclusive_end_timestamp_label:
            si.inclusive_begin_timestamp_label = inbox_message.subscription_information.inclusive_begin_timestamp_label
        si.save()
        inbox_message_db.subscription_information = si
    
    inbox_message_db.received_via = inbox_service
    inbox_message_db.original_message = inbox_message.to_xml()
    inbox_message_db.content_block_count = len(inbox_message.content_blocks)
    inbox_message_db.content_blocks_saved = 0
    inbox_message_db.save()
    
    #Add the content blocks to the database
    saved_blocks = 0
    for content_block in inbox_message.content_blocks:
        binding_id = content_block.content_binding.binding_id
        subtype_id = None
        if len(content_block.content_binding.subtype_ids) > 0:
            subtype_id = content_block.content_binding.subtype_ids[0]
        
        saved = False
        try:
            cb = models.ContentBlock()
            #TODO: Should this create previously unknown content binding/subtypes?
            #TODO: This will throw errors - how should they be handled?
            cb.content_binding_and_subtype = models.ContentBindingAndSubtype.objects.get(content_binding__binding_id=binding_id, subtype__subtype_id=subtype_id)
            cb.content = content_block.content
            if content_block.padding:
                cb.padding = content_block.padding
            if content_block.message:
                cb.message = content_block.message
            cb.inbox_message = inbox_message_db
            #TODO: Not sure what to do about signatures.
            
            #TODO: Currently, the logic is this:
            # If there are not any destination collections, try to add it without a Data Collection
            # If there are destination collections, try to add it to each data collection, but don't add it without a data collection
            # Should there be a way to add it to some kind of "null" data collection that happens even when there are specified data collection(s)?
            
            if len(collections) == 0 and is_content_supported(inbox_service, content_block):
                cb.save()#This adds the content block without associating it to a Data Collection
                saved = True
            
            for collection in collections:
                #print "looking at collection", collection
                if is_content_supported(collection, content_block):
                    #print "content is supported!"
                    if not saved:
                        cb.save()
                        saved = True
                    collection.content_blocks.add(cb)
                else:
                    print 'content is not supported:', content_block.content_binding
            
            if saved and inbox_message.result_id:
                cb.result_id = inbox_message.result_id
                cb.save()
            
            if saved:
                saved_blocks += 1
        except:#TODO: Something useful here.
            raise
    print 'saved blocks should be updated'
    inbox_message_db.content_blocks_saved = saved_blocks
    inbox_message_db.save()
    
    status_message = tm11.StatusMessage(message_id = tm11.generate_message_id(), in_response_to=inbox_message.message_id, status_type = tm11.ST_SUCCESS)
    return status_message
    

def poll_request_handler(poll_service, poll_request, django_request):
    try:
        collection = poll_service.data_collections.get(name=poll_request.collection_name)
    except:
        sm = tm11.StatusMessage(tm11.generate_message_id(), in_response_to=poll_request.message_id, status_type = tm11.ST_NOT_FOUND)
        sm.message = 'The collection you requested was not found'
        sm.status_detail = {'ITEM': poll_request.collection_name}
        return sm
    
    filter_kwargs = {}
    
    if collection.type == 'feed':#Only data feeds care about timestamp labels
        current_datetime = datetime.datetime.now(tzutc())
        
        #If the request specifies a timestamp label in an acceptable range, use it. Otherwise, don't use a begin timestamp label
        if poll_request.exclusive_begin_timestamp_label  and (poll_request.exclusive_begin_timestamp_label < current_datetime):
            filter_kwargs['timestamp_label__gt'] = poll_request.exclusive_begin_timestamp_label
        
        #Use either the specified end timestamp label; or the current time iff the specified end timestmap label is after the current time
        if poll_request.inclusive_end_timestamp_label  and (poll_request.inclusive_end_timestamp_label < current_datetime):
            filter_kwargs['timestamp_label__lte'] = inclusive_end_timestamp_label
        else:
            filter_kwargs['timestamp_label__lte'] = current_datetime
    
    #Set all aspects of a Poll Request to their defaults
    allow_asynch = False
    response_type = 'FULL'
    content_binding = None
    query = None
    delivery_parameters = None
    
    if poll_request.subscription_id:
        try:
            subscription = models.Subscription.get(subscription_id = poll_request.subscription_id)
        except:
            sm = tm11.StatusMessage(tm11.generate_message_id(), in_response_to=poll_request.message_id, status_type=tm11.ST_NOT_FOUND)
            sm.message = 'The Subscription was not found!'
            sm.status_detail = {'ITEM': poll_request.subscription_id}
            return sm
        
        if subscription.status != 'ACTIVE':
            raise Exception("Subscription not active!")#TODO: Status Message
        
        #allow_asynch = subscription.allow_asynch; MSD: This isn't in a subscription???
        response_type = subscription.response_type
        content_bindings = subscription.content_binding_and_subtype.all()#TODO: remediate this with the poll request poll parameters version
        query = tdq.DefaultQuery.from_xml(subscription.query)
        delivery_parameters = subscription.push_parameters
    elif poll_request.poll_parameters:
        allow_asynch = poll_request.poll_parameters.allow_asynch == 'true'
        response_type = poll_request.poll_parameters.response_type
        query = poll_request.poll_parameters.query
        
        content_bindings = []
        for content_binding in poll_request.poll_parameters.content_bindings:
            #TOOD: These can throw an error, handle it better
            #      The error can probably be safely ignored since if the system doesn't know the content binding / subtype, there isn't
            #      any content that matches it anyway
            if len(content_binding.subtype_ids) == 0:
                content_bindings.append(models.ContentBindingAndSubtype.objects.get(content_binding__binding_id = content_binding.binding_id, subtype__subtype_id = None))
            for subtype_id in content_binding.subtype_ids:
                content_bindings.append(models.ContentBindingAndSubtype.objects.get(content_binding__binding_id = content_binding.binding_id, subtype__subtype_id = subtype_id))
        
        delivery_parameters = poll_request.poll_parameters.delivery_parameters#TODO: Remediate with database object
    else:
        raise Exception("Bad message!")#TODO: Return a status message
    
    if len(content_bindings) > 0:#A filter has been specified in the request or the subscription
        filter_kwargs['content_binding_and_subtype__in'] = content_bindings
    
    #print filter_kwargs
    results = collection.content_blocks.filter(**filter_kwargs).order_by('timestamp_label')
    
    if poll_request.poll_parameters.query is not None:
        #TODO: convert query to an XPath statement
        # run xpath against each content block
        # or, maybe have a separate/pluggable query processor for query?
        pass
    
    poll_response = tm11.PollResponse(message_id = tm11.generate_message_id(), in_response_to = poll_request.message_id, collection_name = collection.name)
    
    poll_response.more = False
    poll_response.result_part_number = 1
    
    #TODO: Add support for subscriptions
    
    #What about asynch?
    #What about delivery params?
    #While in this code base there's not really a need for either, as results can always be sent in one response (maybe... maybe not now that i think about it)
    # having code that demonstrates all options makes sense
    
    poll_response.record_count = tm11.RecordCount(len(results), False)
    
    if poll_request.poll_parameters.response_type == tm11.RT_FULL:
        for result in results:
            content_binding = tm11.ContentBinding(result.content_binding_and_subtype.content_binding.binding_id)
            if result.content_binding_and_subtype.subtype:
                content_binding.subtype_ids.append(result.content_binding_and_subtype.subtype.subtype_id)
            cb = tm11.ContentBlock(content_binding = content_binding, content = result.content, padding = result.padding)
            if result.timestamp_label:
                cb.timestamp_label = result.timestamp_label
            poll_response.content_blocks.append(cb)
    
    return poll_response
    
def collection_information_handler(collection_management_service, collection_information_request, django_request):
    cir = tm11.CollectionInformationResponse(message_id = tm11.generate_message_id(), in_response_to = collection_information_request.message_id)
    for collection in collection_management_service.advertised_collections.all():
        ci = tm11.CollectionInformation(
            collection_name = collection.name,
            collection_description = collection.description,
            supported_contents = get_supported_content(collection),
            available = True,
            push_methods = get_push_methods(collection),
            polling_service_instances = get_polling_service_instances(collection),
            subscription_methods = get_subscription_methods(collection),
            collection_volume = None,#TODO: Maybe add this to the model?
            collection_type = collection.type,
            receiving_inbox_services = get_receiving_inbox_services(collection),
        )
        
        cir.append(ci)
    
    return cir

def subscription_management_handler(collection_management_service, taxii_request, django_request):
    pass
    

