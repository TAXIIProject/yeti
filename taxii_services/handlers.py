# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import logging
import datetime
from dateutil.tz import tzutc
#from django.http import HttpResponse
from django.core.urlresolvers import reverse
from taxii_services.models import Inbox, DataCollection, ContentBlock, ContentBindingId, ResultSet
from taxii_services.utils import make_safe
import libtaxii as t
import libtaxii.messages_11 as tm11
import libtaxii.taxii_default_query as tdq
#from lxml import etree
import StringIO
import query_helpers as qh
import re
import os.path
import taxii_web_utils.response_utils as response_utils

#I was writing a lot of code like:
# if request.is_secure():
#   headers = response_utils.TAXII_11_HTTPS_Headers
#else:
#    headers = response_utils.TAXII_11_HTTP_Headers
#
# So i tried to shorten the amount of code it took to get the right headers.
# Maybe that's the wrong thing and maybe the headers should be
# defined in the app configuration file..... i don't know

def get_response_headers(taxii_version='1.1', is_secure=True):
    if taxii_version == '1.1':
        if is_secure:
            return response_utils.TAXII_11_HTTPS_Headers
        else:
            return response_utils.TAXII_11_HTTP_Headers
    elif taxii_version == '1.0':
        if is_secure:
            return response_utils.TAXII_10_HTTPS_Headers
        else:
            return response_utils.TAXII_10_HTTP_Headers
    else:
        raise 'unknown TAXII Version. Must be \'1.1\' or \'1.0\''

def inbox_add_content(request, inbox_name, taxii_message):
    """Adds content to inbox and associated data collections"""
    logger = logging.getLogger('taxii_services.utils.handlers.inbox_add_content')
    logger.debug('Adding content to inbox [%s]', make_safe(inbox_name))
    
    headers = get_response_headers('1.1', request.is_secure)
    
    if len(taxii_message.destination_collection_names) > 0:
        logger.debug('Client specified a Destination Collection Name, which is not supported by YETI.')
        m = tm11.StatusMessage(tm11.generate_message_id(), 
                               taxii_message.message_id, 
                               status_type=tm11.ST_DESTINATION_COLLECTION_ERROR, 
                               message='Destination Collection Names are not allowed')
        
        return response_utils.create_taxii_response(m.to_xml(), headers)
    
    try:
        inbox = Inbox.objects.get(name=inbox_name)
    except:
        logger.debug('Attempting to push content to unknown inbox [%s]', make_safe(inbox_name))
        m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_NOT_FOUND, message='Inbox does not exist [%s]' % (make_safe(inbox_name)))
        return response_utils.create_taxii_response(m.to_xml(), headers)
    
    logger.debug('TAXII message [%s] contains [%d] content blocks', make_safe(taxii_message.message_id), len(taxii_message.content_blocks))
    for content_block in taxii_message.content_blocks:
        try:
            content_binding_id = ContentBindingId.objects.get(binding_id=content_block.content_binding)
        except:
            logger.debug('TAXII message [%s] contained unrecognized content binding [%s]', make_safe(taxii_message.message_id), make_safe(content_block.content_binding))
            continue # cannot proceed - move on to the next content block
            
        if content_binding_id not in inbox.supported_content_bindings.all():
            logger.debug('Inbox [%s] does not accept content with binding id [%s]', make_safe(inbox_name), make_safe(content_block.content_binding))
        else:
            c = ContentBlock()
            c.message_id = taxii_message.message_id
            c.content_binding = content_binding_id
            c.content = content_block.content
            
            if content_block.padding: 
                c.padding = content_block.padding
            
            if request.user.is_authenticated():
                c.submitted_by = request.user
            
            c.save()
            inbox.content_blocks.add(c) # add content block to inbox
            
            for data_collection in inbox.data_collections.all():
                if content_binding_id in data_collection.supported_content_bindings.all():
                    data_collection.content_blocks.add(c)
                    data_collection.save()
                else:
                    logger.debug('Inbox [%s] received data using content binding [%s] - '
                                 'associated data collection [%s] does not support this binding.',
                                 make_safe(inbox_name), make_safe(content_block.content_binding), make_safe(data_collection.name))
    
    inbox.save()
    m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type = tm11.ST_SUCCESS)
    return response_utils.create_taxii_response(m.to_xml(), headers)

def poll_get_content(request, taxii_message):
    """Returns a Poll response for a given Poll Request Message"""
    logger = logging.getLogger('taxii_services.utils.handlers.poll_get_content')
    logger.debug('Polling data from data collection [%s] - begin_ts: %s, end_ts: %s', 
                 make_safe(taxii_message.collection_name), taxii_message.exclusive_begin_timestamp_label, taxii_message.inclusive_end_timestamp_label)
    
    headers = get_response_headers('1.1', request.is_secure)
    
    try:
        data_collection = DataCollection.objects.get(name=taxii_message.collection_name)
    except:
        logger.debug('Attempting to poll unknown data collection [%s]', make_safe(taxii_message.collection_name))
        m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_NOT_FOUND, message='Data collection does not exist [%s]' % (make_safe(taxii_message.collection_name)))
        return response_utils.create_taxii_response(m.to_xml(), headers)
    
    # build query for poll results
    query_params = {}
    if taxii_message.exclusive_begin_timestamp_label:
        query_params['timestamp_label__gt'] = taxii_message.exclusive_begin_timestamp_label
    
    current_datetime = datetime.datetime.now(tzutc())
    if taxii_message.inclusive_end_timestamp_label and (taxii_message.inclusive_end_timestamp_label < current_datetime):
        query_params['timestamp_label__lte'] = taxii_message.inclusive_end_timestamp_label
    else:
        query_params['timestamp_label__lte'] = current_datetime
    
    if taxii_message.poll_parameters.content_bindings:
        query_params['content_binding__in'] = taxii_message.content_bindings
    
    content_blocks = data_collection.content_blocks.filter(**query_params).order_by('timestamp_label')
    logger.debug('Returned [%d] content blocks from data collection [%s]', len(content_blocks), make_safe(data_collection.name))
    
    # TAXII Poll Requests have exclusive begin timestamp label fields, while Poll Responses
    # have *inclusive* begin timestamp label fields. To satisfy this, we add one millisecond
    # to the Poll Request's begin timestamp label. 
    #
    # This will be addressed in future versions of TAXII
    inclusive_begin_ts = None
    if taxii_message.exclusive_begin_timestamp_label:
        inclusive_begin_ts = taxii_message.exclusive_begin_timestamp_label + datetime.timedelta(milliseconds=1)
    
    # build poll response
    poll_response_message = tm11.PollResponse(tm11.generate_message_id(), 
                                            taxii_message.message_id, 
                                            collection_name=data_collection.name, 
                                            exclusive_begin_timestamp_label=inclusive_begin_ts, 
                                            inclusive_end_timestamp_label=query_params['timestamp_label__lte'],
                                            record_count=tm11.RecordCount(len(content_blocks), False))
    
    if taxii_message.poll_parameters.response_type == tm11.RT_FULL:
        for content_block in content_blocks:
            cb = tm11.ContentBlock(tm11.ContentBinding(content_block.content_binding.binding_id), content_block.content, content_block.timestamp_label)
            
            if content_block.padding:
                cb.padding = content_block.padding
            
            poll_response_message.content_blocks.append(cb)
    
    return response_utils.create_taxii_response(poll_response_message.to_xml(), headers)

def query_get_content(request, taxii_message):
    """
    Returns a Poll response for a given Poll Request Message with a query.
    
    This method is intentionally simple (and therefore inefficient). This method
    pulls all potentially matching records from the database, instantiates the 
    content as an etree, then runs an XPath against each etree.
    """
    logger = logging.getLogger('taxii_services.utils.handlers.query_get_content')
    logger.debug('Polling data from data collection [%s]', make_safe(taxii_message.collection_name))
    
    headers = get_response_headers('1.1', request.is_secure)
    
    try:
        data_collection = DataCollection.objects.get(name=taxii_message.collection_name)
    except:
        logger.debug('Attempting to poll unknown data collection [%s]', make_safe(taxii_message.collection_name))
        m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_NOT_FOUND, message='Data collection does not exist [%s]' % (make_safe(taxii_message.collection_name)))
        return response_utils.create_taxii_response(m.to_xml(), headers)
    
    query = taxii_message.poll_parameters.query
    
    #This only supports STIX 1.1 queries
    if query.targeting_expression_id != t.CB_STIX_XML_11:
        m = tm11.StatusMessage(tm11.generate_message_id(), 
                               taxii_message.message_id, 
                               status_type=tdq.ST_UNSUPPORTED_TARGETING_EXPRESSION_ID, 
                               message="Unsupported Targeting Expression ID", 
                               status_detail = {'TARGETING_EXPRESSION_ID': t.CB_STIX_XML_11})
        return response_utils.create_taxii_response(m.to_xml(), headers)
    
    cb = ContentBindingId.objects.get(binding_id=t.CB_STIX_XML_11)
    content_blocks = data_collection.content_blocks.filter(content_binding = cb.id)
    logger.debug('Returned [%d] content blocks to run the query against from data collection [%s]', len(content_blocks), make_safe(data_collection.name))
    matching_content_blocks = []
    
    for block in content_blocks:
        stix_etree = etree.parse(StringIO.StringIO(block.content))
        try:
            if qh.evaluate_criteria(query.criteria, stix_etree):
                matching_content_blocks.append(block)
        except qh.QueryHelperException as qhe:
            logger.debug('There was an error with the query - returning status type: %s; message: %s', qhe.status_type, qhe.message)
            m = tm11.StatusMessage(tm11.generate_message_id(), 
                                   taxii_message.message_id, 
                                   status_type=qhe.status_type, 
                                   message=qhe.message, 
                                   status_detail = qhe.status_detail)
            return response_utils.create_taxii_response(m.to_xml(), headers)
    
    logger.debug('[%d] content blocks match query from data collection [%s]', len(matching_content_blocks), make_safe(data_collection.name))
    
    # Now that we've determined which Content Blocks match the query, 
    # determine whether an Asynchronous Poll will be used.
    #
    # At this point, from a technical perspective, the results are complete and could be 
    # send back to the requester. However, in order to demonstrate the spec, artificial
    # parameters are used to determine whether to use an Asynchronous Poll.
    
    # Here is the super advanced and complex application logic to
    # determine whether the response should be asynchronous
    # modify at your peril
    asynch = False
    text = 'NOT '
    if len(matching_content_blocks) > 2:
        asynch = True
        text = ''
    
    logger.debug('Asyncronous Poll Response will %sbe used', text)
    
    if(asynch):#Send a status message of PENDING and store the results in the DB
        #Check if the client support asynchronous polling
        if taxii_message.poll_parameters.allow_asynch is not True:#We want to do asynch but client doesn't support it. Error
            logger.debug('Client does not support asynch response. Returning FAILURE Status Message.')
            m = tm11.StatusMessage(tm11.generate_message_id(), 
                                   taxii_message.message_id, 
                                   status_type=tm11.ST_FAILURE, 
                                   message='You did not indicate support for Asynchronous Polling, but the server could only send an asynchronous response')
            return response_utils.create_taxii_response(m.to_xml(), headers)
        
        #Create the result ID
        #The result_id ends up looking something like '2014_05_01T12_56_24_403000'
        #This production can be conveniently validated with a regex of ^\d{4}_\d{2}_\d{2}T\d{2}_\d{2}_\d{2}_\d{6}$
        result_id = datetime.datetime.now().isoformat().replace(':','_').replace('-','_').replace('.','_')
        rs = ResultSet()
        rs.result_id = result_id
        rs.data_collection = data_collection
        rs.save()
        rs.content_blocks.add(*matching_content_blocks)
        
        m = tm11.StatusMessage(tm11.generate_message_id(),
                               taxii_message.message_id,
                               status_type = tm11.ST_PENDING,
                               message='Your response is pending. Please request it again at a later time.',
                               status_detail = {'ESTIMATED_WAIT': '0', 'RESULT_ID': result_id, 'WILL_PUSH': False})
        logger.debug('Responding with status message of PENDING, result_id = %s', result_id)
        return response_utils.create_taxii_response(m.to_xml(), headers)
    
    logger.debug('Returning Poll Response')
    
    # build poll response
    poll_response_message = tm11.PollResponse(tm11.generate_message_id(), 
                                              taxii_message.message_id, 
                                              collection_name=data_collection.name,
                                              record_count=tm11.RecordCount(len(matching_content_blocks), False))
    
    if taxii_message.poll_parameters.response_type == tm11.RT_FULL:
        for content_block in matching_content_blocks:
            cb = tm11.ContentBlock(tm11.ContentBinding(content_block.content_binding.binding_id), content_block.content)
            
            if content_block.padding:
                cb.padding = content_block.padding
            
            poll_response_message.content_blocks.append(cb)
    
    return response_utils.create_taxii_response(poll_response_message.to_xml(), headers)

def query_fulfillment(request, taxii_message):
    """
    Returns a Poll response for a given Poll Fulfillment Request.
    
    This method attempts to locate the result id and return it to the requestor.
    No authentication or authorization checks are performed.
    """
    logger = logging.getLogger('taxii_services.utils.handlers.query_get_content')
    
    headers = get_response_headers('1.1', request.is_secure)
    
    r = re.compile('^\d{4}_\d{2}_\d{2}T\d{2}_\d{2}_\d{2}_\d{6}$')
    if not r.match(taxii_message.result_id):#The ID doesn't match - error
        logger.debug('The request result_id did not match the validation regex')
        m = tm11.StatusMessage(tm11.generate_message_id(),
                               taxii_message.message_id,
                               status_type = tm11.NOT_FOUND,
                               message='The requested Result ID was not found.')
        return response_utils.create_taxii_response(m.to_xml(), headers)
    
    try:
        rs = ResultSet.objects.get(result_id = taxii_message.result_id)
    except: #Not found
        logger.debug('The request result_id was not found in the database')
        m = tm11.StatusMessage(tm11.generate_message_id(),
                               taxii_message.message_id,
                               status_type = tm11.ST_NOT_FOUND,
                               message='The requested Result ID was not found.')
        return response_utils.create_taxii_response(m.to_xml(), headers)
    
    poll_response = tm11.PollResponse(tm11.generate_message_id(), 
                                      taxii_message.message_id,
                                      collection_name = rs.data_collection.name)
    if rs.begin_ts is not None:
        poll_response.exclusive_begin_timestamp_label = rs.begin_ts
    if rs.end_ts is not None:
        poll_response.inclusive_end_timestamp_label = rs.end_ts
    
    print 'got %s content blocks' % len(rs.content_blocks.all())
    for block in rs.content_blocks.all():
        cb = tm11.ContentBlock(block.content_binding.binding_id, block.content)
        poll_response.content_blocks.append(cb)
    
    rs.delete()
    
    logger.debug('Returning the result. The result set has been deleted.')
    return response_utils.create_taxii_response(poll_response.to_xml(), headers)

def discovery_get_services(request, taxii_message):
    """Returns a Discovery response for a given Discovery Request Message"""
    logger = logging.getLogger('taxii_services.utils.handlers.discovery_get_services')
    
    headers = get_response_headers('1.1', request.is_secure)
    
    all_services = []
    
    # Inbox Services
    for inbox in Inbox.objects.all():
        service_type = tm11.SVC_INBOX
        inbox_name  = inbox.name
        service_addr   = request.build_absolute_uri(reverse('taxii_services.views.inbox_service', args=[inbox_name]))
        proto_binding = TAXII_PROTO_HTTP_BINDING_ID
        message_bindings = [x.binding_id for x in inbox.supported_message_bindings.all()]
        content_bindings = [tm11.ContentBinding(x.binding_id) for x in inbox.supported_content_bindings.all()]
        available = True # TODO: this should reflect whether or not the user has access to this inbox
       
        service_instance = tm11.DiscoveryResponse.ServiceInstance(service_type=service_type,
                                                                services_version=TAXII_SERVICES_VERSION_ID,
                                                                protocol_binding=proto_binding, 
                                                                service_address=service_addr, 
                                                                message_bindings=message_bindings,
                                                                inbox_service_accepted_content=content_bindings, 
                                                                available=available)
        all_services.append(service_instance)
    
    # Poll Service - not queryable
    all_data_collections = DataCollection.objects.filter(queryable=False)
    if all_data_collections:
        all_data_collection_msg_bindings = set()
        for data_collection in all_data_collections:
            poll_svc_instances = data_collection.poll_service_instances.all()
            
            for poll_svc_instance in poll_svc_instances:
                message_bindings = [x.binding_id for x in poll_svc_instance.message_bindings.all()]
                all_data_collection_msg_bindings.update(message_bindings)
            
        
        service_instance = tm11.DiscoveryResponse.ServiceInstance(service_type=tm11.SVC_POLL, 
                                                                services_version=TAXII_SERVICES_VERSION_ID, 
                                                                protocol_binding=TAXII_PROTO_HTTP_BINDING_ID, 
                                                                service_address=request.build_absolute_uri(reverse('taxii_services.views.poll_service')),
                                                                message_bindings=all_data_collection_msg_bindings,
                                                                available=True)
        all_services.append(service_instance)
    
    #Poll Service - queryable
    queryable_collections = DataCollection.objects.filter(queryable=True)
    if queryable_collections:
        queryable_collections_msg_bindings = set()
        for data_collection in queryable_collections:
            poll_svc_instances = data_collection.poll_service_instances.all()
            
            for poll_svc_instance in poll_svc_instances:
                message_bindings = [x.binding_id for x in poll_svc_instance.message_bindings.all()]
                queryable_collections_msg_bindings.update(message_bindings)
        
        #Create the QueryInformation structure
        te = tdq.DefaultQueryInfo.TargetingExpressionInfo(
            targeting_expression_id = t.CB_STIX_XML_11,
            preferred_scope = ['//Hash/Simple_Hash_Value'],
            allowed_scope=['//Address_Value'])
        
        qi = tdq.DefaultQueryInfo([te], [tdq.CM_CORE])
        
        
        service_instance = tm11.DiscoveryResponse.ServiceInstance(service_type=tm11.SVC_POLL, 
                                                                services_version=TAXII_SERVICES_VERSION_ID, 
                                                                protocol_binding=TAXII_PROTO_HTTP_BINDING_ID, 
                                                                service_address=request.build_absolute_uri(reverse('taxii_services.views.query_example_service')),
                                                                message_bindings=all_data_collection_msg_bindings,
                                                                supported_query = [qi],
                                                                available=True)
        all_services.append(service_instance)

    # Discovery Service
    service_instance = tm11.DiscoveryResponse.ServiceInstance(service_type=tm11.SVC_DISCOVERY, 
                                                            services_version=TAXII_SERVICES_VERSION_ID, 
                                                            protocol_binding=TAXII_PROTO_HTTP_BINDING_ID, 
                                                            service_address=request.build_absolute_uri(reverse('taxii_services.views.discovery_service')),
                                                            message_bindings=[TAXII_MESSAGE_XML_BINDING_ID],
                                                            available=True)
    all_services.append(service_instance)
    logger.debug('Returning [%s] services', len(all_services))
    
    # Build response
    discovery_response_message = tm11.DiscoveryResponse(message_id=tm11.generate_message_id(), 
                                                      in_response_to=taxii_message.message_id,
                                                      service_instances=all_services)
    
    return response_utils.create_taxii_response(discovery_response_message.to_xml(), headers)

