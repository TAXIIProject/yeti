# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import logging
import datetime
from dateutil.tz import tzutc
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from taxii_services.models import Inbox, DataFeed, ContentBlock, ContentBindingId
import libtaxii as t
import libtaxii.messages as tm


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
                                 DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE: [t.VID_TAXII_XML_10],
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
TAXII_SERVICES_VERSION_ID = "urn:taxii.mitre.org:services:1.0"

# TAXII Protocol IDs
TAXII_PROTO_HTTP_BINDING_ID     = "urn:taxii.mitre.org:protocol:http:1.0"
TAXII_PROTO_HTTPS_BINDING_ID    = "urn:taxii.mitre.org:protocol:https:1.0"

# TAXII Message Binding IDs
TAXII_MESSAGE_XML_BINDING_ID    = "urn:taxii.mitre.org:message:xml:1.0"

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
    response[HTTP_HEADER_X_TAXII_CONTENT_TYPE] = t.VID_TAXII_XML_10
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
        msg = "Required headers not present: [%s]" % (', '.join([DICT_REVERSE_DJANGO_NORMALIZATION[x] for x in missing_required_headers])) 
        m = tm.StatusMessage(tm.generate_message_id(), request_message_id, status_type=tm.ST_FAILURE, message=msg)
        return create_taxii_response(m, use_https=request.is_secure())

    #For headers that exist, make sure the values are supported
    for header in DICT_TAXII_HTTP_HEADER_VALUES:
        if header not in request.META:
            continue

        header_value = request.META[header]
        supported_values = DICT_TAXII_HTTP_HEADER_VALUES[header]
        
        if header_value not in supported_values:
            msg = 'The value of %s is not supported. The value was %s. Supported values are %s' % (DICT_REVERSE_DJANGO_NORMALIZATION[header], header_value, supported_values)
            m = tm.StatusMessage(tm.generate_message_id(), request_message_id, status_type=tm.ST_FAILURE, message=msg)
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
        m = tm.StatusMessage(tm.generate_message_id(), request_message_id, status_type=tm.ST_FAILURE, message=msg)
        return create_taxii_response(m, use_https=request.is_secure())
    
    # At this point, the header values are known to be good.
    return None

def validate_taxii_request(request):
    """Validates the broader request parameters and request type for a TAXII exchange"""
    logger = logging.getLogger("taxii_services.utils.handlers.validate_taxii_request")
    logger.debug('attempting to validate request')
    
    if request.method != 'POST':
        logger.info('request was not POST - returning error')
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_FAILURE, message='Request must be POST')
        return create_taxii_response(m, use_https=request.is_secure())
    
    header_validation_resp = validate_taxii_headers(request, '0') # TODO: What to use for request message id?
    if header_validation_resp: # If response is not None an validation of the TAXII headers failed
        return header_validation_resp
    
    if len(request.body) == 0:
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_FAILURE, message='No POST data')
        logger.info('Request had a body length of 0. Returning error.')
        return create_taxii_response(m, use_https=request.is_secure())
    return None

def inbox_add_content(request, inbox_name, taxii_message):
    """Adds content to inbox and associated data feeds"""
    logger = logging.getLogger('taxii_services.utils.handlers.inbox_add_content')
    logger.debug('adding content to inbox [%s]' % (inbox_name))

    try:
        inbox = Inbox.objects.get(name=inbox_name)
    except:
        logger.debug('attempting to push content to unknown inbox [%s]' % (inbox_name))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_NOT_FOUND, message='Inbox does not exist [%s]' % (inbox_name))
        return create_taxii_response(m, use_https=request.is_secure())
    
    logger.debug('taxii message [%s] contains [%d] content blocks' %(taxii_message.message_id, len(taxii_message.content_blocks)))
    for content_block in taxii_message.content_blocks:
        try:
            content_binding_id = ContentBindingId.objects.get(binding_id=content_block.content_binding)
        except:
            logger.debug('taxii message [%s] contained unrecognized content binding [%s]' % (taxii_message.message_id, content_block.content_binding))
        
        if content_binding_id not in inbox.supported_content_bindings.all():
            logger.info('inbox [%s] does not accept content [%s]' % content_block.content_binding)
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
            
            for data_feed in inbox.data_feeds.all():
                if content_binding_id in data_feed.supported_content_bindings.all():
                    data_feed.content_blocks.add(c)
                    data_feed.save()
                else:
                    logger.debug('inbox [%s] received data using content binding [%s] - associated data feed [%s] does not support this binding. ')
    
    inbox.save()
    m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type = tm.ST_SUCCESS)
    return create_taxii_response(m, use_https=request.is_secure())

def poll_get_content(request, taxii_message):
    """Returns a Poll response for a given Poll Request Message"""
    logger = logging.getLogger('taxii_services.utils.handlers.poll_get_content')
    logger.debug('polling data from data feed [%s]' % taxii_message.feed_name)
    logger.debug('begin_ts: %s, end_ts: %s' % (taxii_message.exclusive_begin_timestamp_label, taxii_message.inclusive_end_timestamp_label))
    
    try:
        data_feed = DataFeed.objects.get(name=taxii_message.feed_name)
    except:
        logger.debug('attempting to poll unknown data feed [%s]' % (taxii_message.feed_name))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_NOT_FOUND, message='Data feed does not exist [%s]' % (taxii_message.feed_name))
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
    
    if taxii_message.content_bindings:
        query_params['content_binding__in'] = taxii_message.content_bindings
    
    content_blocks = data_feed.content_blocks.filter(**query_params).order_by('timestamp_label')
    logger.debug('returned %d content blocks from data feed' % (len(content_blocks)))
    
    # TAXII Poll Requests have exclusive begin timestamp label fields, while Poll Responses
    # have *inclusive* begin timestamp label fields. To satisfy this, we add one millisecond
    # to the Poll Request's begin timestamp label. 
    #
    # This will be addressed in future versions of TAXII
    inclusive_begin_ts = None
    if taxii_message.exclusive_begin_timestamp_label:
        inclusive_begin_ts = taxii_message.exclusive_begin_timestamp_label + datetime.timedelta(milliseconds=1)
    
    # build poll response
    poll_response_message = tm.PollResponse(tm.generate_message_id(), 
                                            taxii_message.message_id, 
                                            feed_name=data_feed.name, 
                                            inclusive_begin_timestamp_label=inclusive_begin_ts, 
                                            inclusive_end_timestamp_label=query_params['timestamp_label__lte'])
    
    for content_block in content_blocks:
        cb = tm.ContentBlock(content_block.content_binding.binding_id, content_block.content, content_block.timestamp_label)
        
        if content_block.padding:
            cb.padding = content_block.padding
        
        poll_response_message.content_blocks.append(cb)
    
    return create_taxii_response(poll_response_message, use_https=request.is_secure())

def discovery_get_services(request, taxii_message):
    """Returns a Discovery response for a given Discovery Request Message"""
    logger = logging.getLogger('taxii_services.utils.handlers.discovery_get_services')
    all_services = []
    
    # Inbox Services
    for inbox in Inbox.objects.all():
        service_type = tm.SVC_INBOX
        inbox_name  = inbox.name
        service_addr   = request.build_absolute_uri(reverse('taxii_services.views.inbox_service', args=[inbox_name]))
        proto_binding = TAXII_PROTO_HTTP_BINDING_ID
        message_bindings = [x.binding_id for x in inbox.supported_message_bindings.all()]
        content_bindings = [x.binding_id for x in inbox.supported_content_bindings.all()]
        available = True # TODO: this should reflect whether or not the authenticated user has access to this inbox
       
        service_instance = tm.DiscoveryResponse.ServiceInstance(service_type=service_type,
                                                                services_version=TAXII_SERVICES_VERSION_ID,
                                                                protocol_binding=proto_binding, 
                                                                service_address=service_addr, 
                                                                message_bindings=message_bindings,
                                                                inbox_service_accepted_content=content_bindings, 
                                                                available=available)
        all_services.append(service_instance)
    
    # Poll Service
    all_data_feeds = DataFeed.objects.all()
    if all_data_feeds:
        all_data_feed_msg_bindings = set()
        for data_feed in all_data_feeds:
            poll_svc_instances = data_feed.poll_service_instances.all()
            
            for poll_svc_instance in poll_svc_instances:
                message_bindings = [x.binding_id for x in poll_svc_instance.message_bindings.all()]
                all_data_feed_msg_bindings.update(message_bindings)
            
        
        service_instance = tm.DiscoveryResponse.ServiceInstance(service_type=tm.SVC_POLL, 
                                                                services_version=TAXII_SERVICES_VERSION_ID, 
                                                                protocol_binding=TAXII_PROTO_HTTP_BINDING_ID, 
                                                                service_address=request.build_absolute_uri(reverse('taxii_services.views.poll_service')),
                                                                message_bindings=all_data_feed_msg_bindings,
                                                                available=True)
        all_services.append(service_instance)


    # Discovery Service
    service_instance = tm.DiscoveryResponse.ServiceInstance(service_type=tm.SVC_DISCOVERY, 
                                                            services_version=TAXII_SERVICES_VERSION_ID, 
                                                            protocol_binding=TAXII_PROTO_HTTP_BINDING_ID, 
                                                            service_address=request.build_absolute_uri(reverse('taxii_services.views.discovery_service')),
                                                            message_bindings=[TAXII_MESSAGE_XML_BINDING_ID],
                                                            available=True)
    all_services.append(service_instance)
    
    # Build response
    discovery_response_message = tm.DiscoveryResponse(message_id=tm.generate_message_id(), 
                                                      in_response_to=taxii_message.message_id,
                                                      service_instances=all_services)
    
    return create_taxii_response(discovery_response_message, use_https=request.is_secure())
