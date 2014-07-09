# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import logging
import datetime
from dateutil.tz import tzutc
from django.core.urlresolvers import reverse
from taxiiweb.models import InboxService, DataCollection, ContentBlock, ContentBinding#, ResultSet
from taxii_services.utils import make_safe
import libtaxii as t
import libtaxii.messages_11 as tm11
import libtaxii.taxii_default_query as tdq
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

# def query_get_content(request, taxii_message):
    # """
    # Returns a Poll response for a given Poll Request Message with a query.
    
    # This method is intentionally simple (and therefore inefficient). This method
    # pulls all potentially matching records from the database, instantiates the 
    # content as an etree, then runs an XPath against each etree.
    # """
    # logger = logging.getLogger('taxii_services.utils.handlers.query_get_content')
    # logger.debug('Polling data from data collection [%s]', make_safe(taxii_message.collection_name))
    
    # headers = get_response_headers('1.1', request.is_secure)
    
    # try:
        # data_collection = DataCollection.objects.get(name=taxii_message.collection_name)
    # except:
        # logger.debug('Attempting to poll unknown data collection [%s]', make_safe(taxii_message.collection_name))
        # m = tm11.StatusMessage(tm11.generate_message_id(), taxii_message.message_id, status_type=tm11.ST_NOT_FOUND, message='Data collection does not exist [%s]' % (make_safe(taxii_message.collection_name)))
        # return response_utils.create_taxii_response(m.to_xml(), headers)
    
    # query = taxii_message.poll_parameters.query
    
    # #This only supports STIX 1.1 queries
    # if query.targeting_expression_id != t.CB_STIX_XML_11:
        # m = tm11.StatusMessage(tm11.generate_message_id(), 
                               # taxii_message.message_id, 
                               # status_type=tdq.ST_UNSUPPORTED_TARGETING_EXPRESSION_ID, 
                               # message="Unsupported Targeting Expression ID", 
                               # status_detail = {'TARGETING_EXPRESSION_ID': t.CB_STIX_XML_11})
        # return response_utils.create_taxii_response(m.to_xml(), headers)
    
    # cb = ContentBindingId.objects.get(binding_id=t.CB_STIX_XML_11)
    # content_blocks = data_collection.content_blocks.filter(content_binding = cb.id)
    # logger.debug('Returned [%d] content blocks to run the query against from data collection [%s]', len(content_blocks), make_safe(data_collection.name))
    # matching_content_blocks = []
    
    # for block in content_blocks:
        # stix_etree = etree.parse(StringIO.StringIO(block.content))
        # try:
            # if qh.evaluate_criteria(query.criteria, stix_etree):
                # matching_content_blocks.append(block)
        # except qh.QueryHelperException as qhe:
            # logger.debug('There was an error with the query - returning status type: %s; message: %s', qhe.status_type, qhe.message)
            # m = tm11.StatusMessage(tm11.generate_message_id(), 
                                   # taxii_message.message_id, 
                                   # status_type=qhe.status_type, 
                                   # message=qhe.message, 
                                   # status_detail = qhe.status_detail)
            # return response_utils.create_taxii_response(m.to_xml(), headers)
    
    # logger.debug('[%d] content blocks match query from data collection [%s]', len(matching_content_blocks), make_safe(data_collection.name))
    
    # # Now that we've determined which Content Blocks match the query, 
    # # determine whether an Asynchronous Poll will be used.
    # #
    # # At this point, from a technical perspective, the results are complete and could be 
    # # send back to the requester. However, in order to demonstrate the spec, artificial
    # # parameters are used to determine whether to use an Asynchronous Poll.
    
    # # Here is the super advanced and complex application logic to
    # # determine whether the response should be asynchronous
    # # modify at your peril
    # asynch = False
    # text = 'NOT '
    # if len(matching_content_blocks) > 2:
        # asynch = True
        # text = ''
    
    # logger.debug('Asyncronous Poll Response will %sbe used', text)
    
    # if(asynch):#Send a status message of PENDING and store the results in the DB
        # #Check if the client support asynchronous polling
        # if taxii_message.poll_parameters.allow_asynch is not True:#We want to do asynch but client doesn't support it. Error
            # logger.debug('Client does not support asynch response. Returning FAILURE Status Message.')
            # m = tm11.StatusMessage(tm11.generate_message_id(), 
                                   # taxii_message.message_id, 
                                   # status_type=tm11.ST_FAILURE, 
                                   # message='You did not indicate support for Asynchronous Polling, but the server could only send an asynchronous response')
            # return response_utils.create_taxii_response(m.to_xml(), headers)
        
        # #Create the result ID
        # #The result_id ends up looking something like '2014_05_01T12_56_24_403000'
        # #This production can be conveniently validated with a regex of ^\d{4}_\d{2}_\d{2}T\d{2}_\d{2}_\d{2}_\d{6}$
        # result_id = datetime.datetime.now().isoformat().replace(':','_').replace('-','_').replace('.','_')
        # rs = ResultSet()
        # rs.result_id = result_id
        # rs.data_collection = data_collection
        # rs.save()
        # rs.content_blocks.add(*matching_content_blocks)
        
        # m = tm11.StatusMessage(tm11.generate_message_id(),
                               # taxii_message.message_id,
                               # status_type = tm11.ST_PENDING,
                               # message='Your response is pending. Please request it again at a later time.',
                               # status_detail = {'ESTIMATED_WAIT': '0', 'RESULT_ID': result_id, 'WILL_PUSH': False})
        # logger.debug('Responding with status message of PENDING, result_id = %s', result_id)
        # return response_utils.create_taxii_response(m.to_xml(), headers)
    
    # logger.debug('Returning Poll Response')
    
    # # build poll response
    # poll_response_message = tm11.PollResponse(tm11.generate_message_id(), 
                                              # taxii_message.message_id, 
                                              # collection_name=data_collection.name,
                                              # record_count=tm11.RecordCount(len(matching_content_blocks), False))
    
    # if taxii_message.poll_parameters.response_type == tm11.RT_FULL:
        # for content_block in matching_content_blocks:
            # cb = tm11.ContentBlock(tm11.ContentBinding(content_block.content_binding.binding_id), content_block.content)
            
            # if content_block.padding:
                # cb.padding = content_block.padding
            
            # poll_response_message.content_blocks.append(cb)
    
    # return response_utils.create_taxii_response(poll_response_message.to_xml(), headers)

# def query_fulfillment(request, taxii_message):
    # """
    # Returns a Poll response for a given Poll Fulfillment Request.
    
    # This method attempts to locate the result id and return it to the requestor.
    # No authentication or authorization checks are performed.
    # """
    # logger = logging.getLogger('taxii_services.utils.handlers.query_get_content')
    
    # headers = get_response_headers('1.1', request.is_secure)
    
    # r = re.compile('^\d{4}_\d{2}_\d{2}T\d{2}_\d{2}_\d{2}_\d{6}$')
    # if not r.match(taxii_message.result_id):#The ID doesn't match - error
        # logger.debug('The request result_id did not match the validation regex')
        # m = tm11.StatusMessage(tm11.generate_message_id(),
                               # taxii_message.message_id,
                               # status_type = tm11.NOT_FOUND,
                               # message='The requested Result ID was not found.')
        # return response_utils.create_taxii_response(m.to_xml(), headers)
    
    # try:
        # rs = ResultSet.objects.get(result_id = taxii_message.result_id)
    # except: #Not found
        # logger.debug('The request result_id was not found in the database')
        # m = tm11.StatusMessage(tm11.generate_message_id(),
                               # taxii_message.message_id,
                               # status_type = tm11.ST_NOT_FOUND,
                               # message='The requested Result ID was not found.')
        # return response_utils.create_taxii_response(m.to_xml(), headers)
    
    # poll_response = tm11.PollResponse(tm11.generate_message_id(), 
                                      # taxii_message.message_id,
                                      # collection_name = rs.data_collection.name)
    # if rs.begin_ts is not None:
        # poll_response.exclusive_begin_timestamp_label = rs.begin_ts
    # if rs.end_ts is not None:
        # poll_response.inclusive_end_timestamp_label = rs.end_ts
    
    # print 'got %s content blocks' % len(rs.content_blocks.all())
    # for block in rs.content_blocks.all():
        # cb = tm11.ContentBlock(block.content_binding.binding_id, block.content)
        # poll_response.content_blocks.append(cb)
    
    # rs.delete()
    
    # logger.debug('Returning the result. The result set has been deleted.')
    # return response_utils.create_taxii_response(poll_response.to_xml(), headers)
