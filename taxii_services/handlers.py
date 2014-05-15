# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import logging
import datetime
from dateutil.tz import tzutc
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from taxii_services.models import Inbox, DataCollection, ContentBlock, ContentBindingId, ResultSet
from taxii_services.utils import make_safe
import libtaxii as t
import libtaxii.messages_11 as tm11
import libtaxii.taxii_default_query as tdq
from lxml import etree
import StringIO
import query_helpers as qh
import re
import os.path


# A set of headers that are utilized by TAXII. These are formatted as Django's
# HttpRequest.META keys: https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.REQUEST
DJANGO_HTTP_HEADER_CONTENT_TYPE         = 'CONTENT_TYPE'
DJANGO_HTTP_HEADER_ACCEPT               = 'HTTP_ACCEPT'
DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE = 'HTTP_X_TAXII_CONTENT_TYPE'
DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL     = 'HTTP_X_TAXII_PROTOCOL'
DJANGO_HTTP_HEADER_X_TAXII_ACCEPT       = 'HTTP_X_TAXII_ACCEPT'
DJANGO_HTTP_HEADER_X_TAXII_SERVICES     = 'HTTP_X_TAXII_SERVICES'

# A list of request headers that are required by TAXII
DICT_REQUIRED_TAXII_HTTP_HEADERS = (DJANGO_HTTP_HEADER_CONTENT_TYPE, 
                                    DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE,
                                    DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL)

#For each TAXII Header that may appear in a request, a list of the values this application supports
DICT_TAXII_HTTP_HEADER_VALUES = {DJANGO_HTTP_HEADER_ACCEPT: ['application/xml'],
                                 DJANGO_HTTP_HEADER_CONTENT_TYPE: ['application/xml'],
                                 DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE: [t.VID_TAXII_XML_11],
                                 DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL: [t.VID_TAXII_HTTPS_10, t.VID_TAXII_HTTP_10]}

# A set of headers that are utilized by TAXII. These are formatted using HTTP header conventions
HTTP_HEADER_CONTENT_TYPE            = 'Content-Type'
HTTP_HEADER_ACCEPT                  = 'Accept'
HTTP_HEADER_X_TAXII_CONTENT_TYPE    = 'X-TAXII-Content-Type'
HTTP_HEADER_X_TAXII_PROTOCOL        = 'X-TAXII-Protocol'
HTTP_HEADER_X_TAXII_ACCEPT          = 'X-TAXII-Accept'
HTTP_HEADER_X_TAXII_SERVICES        = 'X-TAXII-Services'

# Dictionary for mapping Django's HttpRequest.META headers to actual HTTP headers
DICT_REVERSE_DJANGO_NORMALIZATION = {DJANGO_HTTP_HEADER_CONTENT_TYPE: HTTP_HEADER_CONTENT_TYPE,
                                     DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE: HTTP_HEADER_X_TAXII_CONTENT_TYPE,
                                     DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL: HTTP_HEADER_X_TAXII_PROTOCOL,
                                     DJANGO_HTTP_HEADER_ACCEPT: HTTP_HEADER_ACCEPT}

# TAXII Services Version ID
TAXII_SERVICES_VERSION_ID = "urn:taxii.mitre.org:services:1.1"

# TAXII Protocol IDs
TAXII_PROTO_HTTP_BINDING_ID     = "urn:taxii.mitre.org:protocol:http:1.0"
TAXII_PROTO_HTTPS_BINDING_ID    = "urn:taxii.mitre.org:protocol:https:1.0"

# TAXII Message Binding IDs
TAXII_MESSAGE_XML_BINDING_ID    = "urn:taxii.mitre.org:message:xml:1.1"

# HTTP status codes
HTTP_STATUS_OK              = 200
HTTP_STATUS_SERVER_ERROR    = 500
HTTP_STATUS_NOT_FOUND       = 400

def create_taxii_response(message, status_code=HTTP_STATUS_OK, use_https=True):
    """Creates a TAXII HTTP Response for a given message and status code"""
    resp = HttpResponse()
    resp.content = message.to_xml()
    set_taxii_headers_response(resp, use_https)
    resp.status_code = status_code
    return resp

def set_taxii_headers_response(response, use_https):
    """Sets the TAXII HTTP Headers for a given HTTP response"""
    response[HTTP_HEADER_CONTENT_TYPE] = 'application/xml'
    response[HTTP_HEADER_X_TAXII_CONTENT_TYPE] = t.VID_TAXII_XML_11
    protocol = t.VID_TAXII_HTTPS_10 if use_https else t.VID_TAXII_HTTP_10
    response[HTTP_HEADER_X_TAXII_PROTOCOL] = protocol
    return response

def validate_taxii_headers(request, request_message_id):
    """
    Validates TAXII headers. It returns a response containing a TAXII
    status message if the headers were not valid. It returns None if 
    the headers are valid.
    """
    # Make sure the required headers are present
    missing_required_headers = set(DICT_REQUIRED_TAXII_HTTP_HEADERS).difference(set(request.META))
    if missing_required_headers:
        required_headers = ', '.join(DICT_REVERSE_DJANGO_NORMALIZATION[x] for x in missing_required_headers)
        msg = "Required headers not present: [%s]" % (required_headers) 
        m = tm11.StatusMessage(tm11.generate_message_id(), request_message_id, status_type=tm11.ST_FAILURE, message=msg)
        return create_taxii_response(m, use_https=request.is_secure())

    #For headers that exist, make sure the values are supported
    for header in DICT_TAXII_HTTP_HEADER_VALUES:
        if header not in request.META:
            continue

        header_value = request.META[header]
        supported_values = DICT_TAXII_HTTP_HEADER_VALUES[header]
        
        if header_value not in supported_values:
            msg = 'The value of %s is not supported. Supported values are %s' % (DICT_REVERSE_DJANGO_NORMALIZATION[header], supported_values)
            m = tm11.StatusMessage(tm11.generate_message_id(), request_message_id, status_type=tm11.ST_FAILURE, message=msg)
            return create_taxii_response(m, use_https=request.is_secure())
    
    # Check to make sure the specified protocol matches the protocol used
    if request.META[DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL] == t.VID_TAXII_HTTPS_10:
        header_proto = 'HTTPS'
    elif request.META[DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL] == t.VID_TAXII_HTTP_10:
        header_proto = 'HTTP'
    else:
        header_proto = 'unknown'
    
    request_proto = 'HTTPS' if request.is_secure() else 'HTTP' # Did the request come over HTTP or HTTPS?
    
    if header_proto != request_proto:
        msg = 'Protocol value incorrect. TAXII header specified %s but was sent over %s' % (header_proto, request_proto)
        m = tm11.StatusMessage(tm11.generate_message_id(), request_message_id, status_type=tm11.ST_FAILURE, message=msg)
        return create_taxii_response(m, use_https=request.is_secure())
    
    # At this point, the header values are known to be good.
    return None

def validate_taxii_request(request):
    """Validates the broader request parameters and request type for a TAXII exchange"""
    logger = logging.getLogger("taxii_services.utils.handlers.validate_taxii_request")
    logger.debug('Attempting to validate request')
    
    if request.method != 'POST':
        logger.info('Request was not POST - returning error')
        m = tm11.StatusMessage(tm11.generate_message_id(), '0', status_type=tm11.ST_FAILURE, message='Request must be POST')
        return create_taxii_response(m, use_https=request.is_secure())
    
    header_validation_resp = validate_taxii_headers(request, '0') # TODO: What to use for request message id?
    if header_validation_resp: # If response is not None an validation of the TAXII headers failed
        logger.info('TAXII header validation failed for reason [%s]', make_safe(header_validation_resp.message))
        return header_validation_resp
    
    if len(request.body) == 0:
        m = tm11.StatusMessage(tm11.generate_message_id(), '0', status_type=tm11.ST_FAILURE, message='No POST data')
        logger.info('Request had a body length of 0. Returning error.')
        return create_taxii_response(m, use_https=request.is_secure())
    
    logger.debug('Request was valid')
    return None

def inbox_add_content(request, inbox_name, taxii_message):
    """Adds content to inbox and associated data collections"""
    logger = logging.getLogger('taxii_services.utils.handlers.inbox_add_content')
    logger.debug('Adding content to inbox [%s]', make_safe(inbox_name))
    
    if len(taxii_message.destination_collection_names) > 0:
        logger.debug('Client specified a Destination Collection Name, which is not supported by YETI.')
        m = tm11.StatusMessage(tm11.generate_message_id(), 
                               taxii_message.message_id, 
                               status_type=tm11.ST_DESTINATION_COLLECTION_ERROR, 
                               message='Destination Collection Names are not allowed')
        return create_taxii_response(m, use_https=request.is_secure())
    
    try:
        inbox = Inbox.objects.get(name=inbox_name)
    except:
        logger.debug('Attempting to push content to unknown inbox [%s]', make_safe(inbox_name))
        m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_NOT_FOUND, message='Inbox does not exist [%s]' % (make_safe(inbox_name)))
        return create_taxii_response(m, use_https=request.is_secure())
    
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
    return create_taxii_response(m, use_https=request.is_secure())

def poll_get_content(request, taxii_message):
    """Returns a Poll response for a given Poll Request Message"""
    logger = logging.getLogger('taxii_services.utils.handlers.poll_get_content')
    logger.debug('Polling data from data collection [%s] - begin_ts: %s, end_ts: %s', 
                 make_safe(taxii_message.collection_name), taxii_message.exclusive_begin_timestamp_label, taxii_message.inclusive_end_timestamp_label)
    
    try:
        data_collection = DataCollection.objects.get(name=taxii_message.collection_name)
    except:
        logger.debug('Attempting to poll unknown data collection [%s]', make_safe(taxii_message.collection_name))
        m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_NOT_FOUND, message='Data collection does not exist [%s]' % (make_safe(taxii_message.collection_name)))
        return create_taxii_response(m, use_https=request.is_secure())
    
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
    
    return create_taxii_response(poll_response_message, use_https=request.is_secure())

def query_get_content(request, taxii_message):
    """
    Returns a Poll response for a given Poll Request Message with a query.
    
    This method is intentionally simple (and therefore inefficient). This method
    pulls all potentially matching records from the database, instantiates the 
    content as an etree, then runs an XPath against each etree.
    """
    logger = logging.getLogger('taxii_services.utils.handlers.query_get_content')
    logger.debug('Polling data from data collection [%s]', make_safe(taxii_message.collection_name))
    
    try:
        data_collection = DataCollection.objects.get(name=taxii_message.collection_name)
    except:
        logger.debug('Attempting to poll unknown data collection [%s]', make_safe(taxii_message.collection_name))
        m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_NOT_FOUND, message='Data collection does not exist [%s]' % (make_safe(taxii_message.collection_name)))
        return create_taxii_response(m, use_https=request.is_secure())
    
    query = taxii_message.poll_parameters.query
    
    #This only supports STIX 1.1 queries
    if query.targeting_expression_id != t.CB_STIX_XML_11:
        m = tm11.StatusMessage(tm11.generate_message_id(), 
                               taxii_message.message_id, 
                               status_type=tdq.ST_UNSUPPORTED_TARGETING_EXPRESSION_ID, 
                               message="Unsupported Targeting Expression ID", 
                               status_detail = {'TARGETING_EXPRESSION_ID': t.CB_STIX_XML_11})
        return create_taxii_response(m, use_https=request.is_secure())
    
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
            return create_taxii_response(m, use_https=request.is_secure())
    
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
            return create_taxii_response(m, use_https=request.is_secure())
        
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
        return create_taxii_response(m, use_https=request.is_secure())
    
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
    
    return create_taxii_response(poll_response_message, use_https=request.is_secure())

def query_fulfillment(request, taxii_message):
    """
    Returns a Poll response for a given Poll Fulfillment Request.
    
    This method attempts to locate the result id and return it to the requestor.
    No authentication or authorization checks are performed.
    """
    logger = logging.getLogger('taxii_services.utils.handlers.query_get_content')
    
    r = re.compile('^\d{4}_\d{2}_\d{2}T\d{2}_\d{2}_\d{2}_\d{6}$')
    if not r.match(taxii_message.result_id):#The ID doesn't match - error
        logger.debug('The request result_id did not match the validation regex')
        m = tm11.StatusMessage(tm11.generate_message_id(),
                               taxii_message.message_id,
                               status_type = tm11.NOT_FOUND,
                               message='The requested Result ID was not found.')
        return create_taxii_response(m, use_https=request.is_secure())
    
    try:
        rs = ResultSet.objects.get(result_id = taxii_message.result_id)
    except: #Not found
        logger.debug('The request result_id was not found in the database')
        m = tm11.StatusMessage(tm11.generate_message_id(),
                               taxii_message.message_id,
                               status_type = tm11.ST_NOT_FOUND,
                               message='The requested Result ID was not found.')
        return create_taxii_response(m, use_https=request.is_secure())
    
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
    return create_taxii_response(poll_response, use_https=request.is_secure())

def discovery_get_services(request, taxii_message):
    """Returns a Discovery response for a given Discovery Request Message"""
    logger = logging.getLogger('taxii_services.utils.handlers.discovery_get_services')
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
    
    return create_taxii_response(discovery_response_message, use_https=request.is_secure())

