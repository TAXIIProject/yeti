# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import logging
from django.http import HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from taxii_services.utils.decorators import taxii_auth_check
import taxii_services.utils.handlers as handlers
import libtaxii.messages as tm


def server_error(request):
    '''
    This overrides the django.views.defaults.server_error view.
    If the request path points to a taxii service, we return a TAXII
    FAILURE message. If the request pointed to something outside of
    the TAXII services, we return a normal HTTP 500 response
    '''
    logger = logging.getLogger('yeti.taxii_services.views.server_error')
    logger.debug('server error occured - returning ST_FAILURE message')
    
    if request.path.startswith('/services'):
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_FAILURE, message='An internal server error occurred')
        return handlers.create_taxii_response(m, handlers.HTTP_STATUS_OK, use_https=request.is_secure()) # should the http status be 500?
    
    resp = HttpResponseServerError()
    resp.body = 'A server error occurred'
    return resp
    
@csrf_exempt
@taxii_auth_check
def inbox_service(request, inbox_name):
    """Handles TAXII Inbox Service requests."""
    logger = logging.getLogger('yeti.taxii_services.views.inbox_service')
    logger.debug('entering inbox service')
    
    resp = handlers.validate_taxii_request(request)
    if resp: return resp # if validation failed, return the response
    
    try:
        taxii_message = tm.get_message_from_xml(request.body)
        logger.debug('received taxii_message [%s]' % (taxii_message.message_id))
    except Exception as ex:
        logger.debug('unable to parse inbound message: %s' % (ex.message))
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_BAD_MESSAGE, message='Message received could not be parsed')
        return handlers.create_taxii_response(m, use_https=request.is_secure())
    
    if taxii_message.message_type != tm.MSG_INBOX_MESSAGE:
        logger.info('taxii taxii_message [%s] was not inbox type [%s]' % (taxii_message.message_id, taxii_message.message_type))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_FAILURE, message='Message sent to inbox service did not have an inbox taxii_message type')
        return handlers.create_taxii_response(m, use_https=request.is_secure())
    
    resp = handlers.inbox_add_content(request, inbox_name, taxii_message)
    return resp

@csrf_exempt
@taxii_auth_check
def poll_service(request):
    """Handles TAXII Poll Service requests."""
    logger = logging.getLogger("yeti.taxii_services.views.poll_service")
    logger.debug('entering poll service')
    
    resp = handlers.validate_taxii_request(request)
    if resp: return resp # if validation failed, return the response
    
    try:
        taxii_message = tm.get_message_from_xml(request.body)
        logger.debug('received taxii message [%s]' % (taxii_message.message_id))
    except Exception as ex:
        logger.debug('unable to parse inbound message: %s' % (ex.message))
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_BAD_MESSAGE, message='Message received could not be parsed')
        return handlers.create_taxii_response(m, use_https=request.is_secure())
    
    if taxii_message.message_type != tm.MSG_POLL_REQUEST:
        logger.info('Message [%s] was not poll request [%s]' % (taxii_message.message_id,taxii_message.message_type))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_FAILURE, message='Message sent to poll service did not have a poll request message type')
        return handlers.create_taxii_response(m, use_https=request.is_secure())    
    
    resp = handlers.poll_get_content(request, taxii_message)
    return resp


