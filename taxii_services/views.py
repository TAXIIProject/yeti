# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import logging
from django.views.decorators.csrf import csrf_exempt
from taxii_services.decorators import taxii_auth_check
import taxii_services.handlers as handlers
from taxii_services.utils import make_safe
import libtaxii.messages_11 as tm11
import taxii_web_utils.request_utils as ru

@csrf_exempt
@taxii_auth_check
def inbox_service(request, inbox_name):
    """Handles TAXII Inbox Service requests."""
    logger = logging.getLogger('yeti.taxii_services.views.inbox_service')
    logger.debug('Entering Inbox service')
    
    taxii_message = ru.validate_and_parse_request(request, ru.TAXII_11_HeaderRules, tm11.InboxMessage, True)
    
    logger.debug('Inbox [%s] received TAXII message with id [%s] and type [%s]', 
                 make_safe(inbox_name), make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
    
    resp = handlers.inbox_add_content(request, inbox_name, taxii_message)
    return resp

@csrf_exempt
@taxii_auth_check
def poll_service(request):
    """Handles TAXII Poll Service requests."""
    logger = logging.getLogger("yeti.taxii_services.views.poll_service")
    logger.debug('Entering poll service')
    
    taxii_message = ru.validate_and_parse_request(request, ru.TAXII_11_HeaderRules, tm11.PollRequest, True)
    
    logger.debug('Poll service received TAXII message with id [%s] and type [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
    
    resp = handlers.poll_get_content(request, taxii_message)
    return resp

@csrf_exempt
@taxii_auth_check
def discovery_service(request):
    """Handles TAXII Discovery Service requests"""
    logger = logging.getLogger('yeti.taxii_services.views.discovery_service')
    logger.debug('Entering discovery service')
    
    taxii_message = ru.validate_and_parse_request(request, ru.TAXII_11_HeaderRules, tm11.DiscoveryRequest, True)
    
    logger.debug('Discovery service received TAXII message with id [%s] and type [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
    
    resp = handlers.discovery_get_services(request, taxii_message)
    return resp

@csrf_exempt
@taxii_auth_check
def query_example_service(request):
    """Handles TAXII Poll Service requests. Supports Query"""
    logger = logging.getLogger('yeti.taxii_services.views.query_example_service')
    logger.debug('Entering poll query service')
    
    taxii_message = ru.validate_and_parse_request(request, ru.TAXII_11_HeaderRules, [tm11.PollRequest, tm11.PollFulfillmentRequest], True)
    
    logger.debug('Poll service (w/ query) received TAXII message with id [%s] and type [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
    
    if taxii_message.message_type == tm11.MSG_POLL_REQUEST:
        resp = handlers.query_get_content(request, taxii_message)
    elif taxii_message.message_type == tm11.MSG_POLL_FULFILLMENT_REQUEST:
        resp = handlers.query_fulfillment(request, taxii_message)
    else:
        raise Exception('uh.... ?')
    
    return resp
