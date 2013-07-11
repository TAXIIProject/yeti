# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import logging
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from decorators import yeti_auth_check
from taxii_services.models import DataFeed, ContentBlock, ContentBindingId
import taxii_services.utils.handlers as handlers
import libtaxii.messages as tm
import yeti.settings


@csrf_exempt
@yeti_auth_check
def inbox_service(request, dest_feed_name):
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
        return handlers.create_taxii_response(m)
    
    if taxii_message.message_type != tm.MSG_INBOX_MESSAGE:
        logger.info('taxii taxii_message [%s] was not inbox type [%s]' % (taxii_message.message_id, taxii_message.message_type))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_FAILURE, message='Message sent to inbox service did not have an inbox taxii_message type')
        return handlers.create_taxii_response(m)
    
    dest_data_feed = DataFeed.objects.filter(name=dest_feed_name)
    if not dest_data_feed:
        logger.debug('attempting to assign content to unknown data feed [%s]' % (dest_feed_name))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_NOT_FOUND, message='Destination feed does not exist [%s]' % (dest_feed_name))
        return handlers.create_taxii_response(m)
    
    logger.debug('taxii message [%s] contains [%d] content blocks' %(taxii_message.message_id, len(taxii_message.content_blocks)))
    for inbox_block in taxii_message.content_blocks:
        content_binding_id = ContentBindingId.objects.filter(binding_id=inbox_block.content_binding)
        
        if not content_binding_id:
            logger.info('taxii message [%s] contained unrecognized content binding [%s]' % (taxii_message.message_id, inbox_block.content_binding))
        else:
            c = ContentBlock()
            c.message_id = taxii_message.message_id
            c.submitted_by = request.user
            c.data_feeds.add(dest_data_feed)
            c.content_binding = content_binding_id
            c.content = inbox_block.content
            if inbox_block.padding: c.padding = inbox_block.padding
            c.save()
    
    m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type = tm.ST_SUCCESS)
    return handlers.create_taxii_response(m)

@csrf_exempt
@yeti_auth_check
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
        return handlers.create_taxii_response(m)
    
    if taxii_message.message_type != tm.MSG_POLL_REQUEST:
        logger.info('Message [%s] was not poll request [%s]' % (taxii_message.message_id,taxii_message.message_type))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_FAILURE, message='Message sent to poll service did not have a poll request message type')
        return handlers.create_taxii_response(m)    
    
    data_feed = DataFeed.objects.filter(name=taxii_message.feed_name)
    if not data_feed:
        logger.debug('attempting to poll unknown data feed [%s]' % (taxii_message.feed_name))
        m = tm.StatusMessage(tm.generate_message_id(), taxii_message.message_id, status_type=tm.ST_NOT_FOUND, message='Data feed does not exist [%s]' % (taxii_message.feed_name))
        return handlers.create_taxii_response(m)
    
    # build query for poll results
    query_params = {'data_feeds' : data_feed}
    
    if taxii_message.exclusive_begin_timestamp_label:
        query_params['timestamp_label__gt'] = taxii_message.exclusive_begin_timestamp_label
    
    current_datetime = datetime.datetime.utcnow()
    if taxii_message.inclusive_end_timestamp_label and (taxii_message.inclusive_end_timestamp_label < current_datetime):
        query_params['timestamp_label__lte'] = taxii_message.exclusive_end_timestamp_label
    else:
        query_params['timestamp_label__lte'] = current_datetime
    
    if taxii_message.content_bindings:
        query_params['content_binding__in'] = taxii_message.content_bindings
    
    content_blocks = ContentBlock.objects.filter(**query_params).order_by('timestamp_label')
    
    # TAXII Poll Requests have exclusive begin timestamp label fields, while Poll Responses
    # have *inclusive* begin timestamp label fields. To satisfy this, we add one millisecond
    # to the Poll Request's begin timestamp label. 
    #
    # This will be addressed in future versions of TAXII
    inclusive_begin_ts = None
    if taxii_message.exclusive_begin_timestamp_label:
        inclusive_begin_ts = taxii_message.exclusive_begin_timestamp_label + datetime.timedelta(milliseconds=1)
    
    poll_response_message = tm.PollResponse(tm.generate_message_id(), 
                                            taxii_message.message_id, 
                                            feed_name=data_feed.name, 
                                            inclusive_begin_timestamp_label=inclusive_begin_ts, 
                                            inclusive_end_timestamp_label=query_params['timestamp_label__lte'])
    
    for block in content_blocks:
        cb = tm.ContentBlock(block.content_binding, block.content, block.timestamp_label)
        
        if block.padding:
            cb.padding = block.padding
        
        poll_response_message.content_blocks.append(cb)
    
    return handlers.create_taxii_response(poll_response_message)


