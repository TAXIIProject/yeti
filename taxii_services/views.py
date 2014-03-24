# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import logging
from django.views.decorators.csrf import csrf_exempt
from taxii_services.decorators import taxii_auth_check
import taxii_services.handlers as handlers
from taxii_services.utils import make_safe
import libtaxii.messages_11 as tm11

    
@csrf_exempt
@taxii_auth_check
def inbox_service(request, inbox_name):
    """Handles TAXII Inbox Service requests."""
    logger = logging.getLogger('yeti.taxii_services.views.inbox_service')
    logger.debug('Entering Inbox service')
    
    resp = handlers.validate_taxii_request(request)
    if resp: return resp # if validation failed, return the response
    
    try:
        taxii_message = tm11.get_message_from_xml(request.body)
    except Exception as ex:
        logger.debug('Unable to parse inbound message: %s', ex.message)
        m = tm11.StatusMessage(tm11.generate_message_id(), '0', status_type=tm11.ST_BAD_MESSAGE, message='Message received could not be parsed')
        return handlers.create_taxii_response(m, use_https=request.is_secure())
    
    logger.debug('Inbox [%s] received TAXII message with id [%s] and type [%s]', 
                 make_safe(inbox_name), make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
    
    if taxii_message.message_type != tm11.MSG_INBOX_MESSAGE:
        logger.info('TAXII message with id [%s] was not Inbox type [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
        m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_FAILURE, message='Message sent to Inbox service did not have an inbox Message type')
        return handlers.create_taxii_response(m, use_https=request.is_secure())
    
    resp = handlers.inbox_add_content(request, inbox_name, taxii_message)
    return resp

@csrf_exempt
@taxii_auth_check
def poll_service(request):
    """Handles TAXII Poll Service requests."""
    logger = logging.getLogger("yeti.taxii_services.views.poll_service")
    logger.debug('Entering poll service')
    
    resp = handlers.validate_taxii_request(request)
    if resp: return resp # if validation failed, return the response
    
    try:
        taxii_message = tm11.get_message_from_xml(request.body)
    except tm11.UnsupportedQueryException as e:
        logger.debug('Unsupported query found in TAXII Message')
        m = tm11.StatusMessage(tm11.generate_message_id(), '0', status_type=tm11.ST_UNSUPPORTED_QUERY, message='The message used an unsupported query format')
        return handlers.create_taxii_response(m, use_https=request.is_secure())
    except Exception as ex:
        logger.debug('Unable to parse inbound message: %s', ex.message)
        m = tm11.StatusMessage(tm11.generate_message_id(), '0', status_type=tm11.ST_BAD_MESSAGE, message='Message received could not be parsed')
        return handlers.create_taxii_response(m, use_https=request.is_secure())
    
    logger.debug('Poll service received TAXII message with id [%s] and type [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
    
    if taxii_message.message_type != tm11.MSG_POLL_REQUEST:
        logger.info('TAXII message with id [%s] was not Poll request [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
        m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_FAILURE, message='Message sent to Poll service did not have a poll request message type')
        return handlers.create_taxii_response(m, use_https=request.is_secure())    
    
    resp = handlers.poll_get_content(request, taxii_message)
    return resp

@csrf_exempt
@taxii_auth_check
def discovery_service(request):
    """Handles TAXII Discovery Service requests"""
    logger = logging.getLogger('yeti.taxii_services.views.discovery_service')
    logger.debug('Entering discovery service')
    
    resp = handlers.validate_taxii_request(request)
    if resp: return resp # if validation fails, return the response
    
    try:
        taxii_message = tm11.get_message_from_xml(request.body)
    except Exception as ex:
        logger.debug('Unable to parse inbound message: %s', ex.message)
        m = tm11.StatusMessage(tm11.generate_message_id(), '0', status_type=tm11.ST_BAD_MESSAGE, message='Message received could not be parsed')
        return handlers.create_taxii_response(m, use_https=request.is_secure())
    
    logger.debug('Discovery service received TAXII message with id [%s] and type [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
    
    if taxii_message.message_type != tm11.MSG_DISCOVERY_REQUEST:
        logger.info('TAXII message with id [%s] was not Discovery request [%s]', make_safe(taxii_message.message_id), make_safe(taxii_message.message_type))
        m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_FAILURE, message='Message sent to discovery service did not have a discovery request message type')
        return handlers.create_taxii_response(m, use_https=request.is_secure())

    resp = handlers.discovery_get_services(request, taxii_message)
    return resp

