# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import logging
from django.http import HttpResponseServerError

import libtaxii.messages_11 as tm11
import taxii_services.handlers as handlers
import taxii_web_utils.response_utils as response_utils

class ProcessExceptionMiddleware(object):
    def process_exception(self, request, exception):
        logger = logging.getLogger('yeti.taxii_services.middleware.ProcessExceptionMiddleware.process_exception')
        logger.exception('Server error occured')
    
        if request.path.startswith('/services'):
            
            logger.debug('Returning ST_FAILURE message')
            m = tm11.StatusMessage(tm11.generate_message_id(), '0', status_type=tm11.ST_FAILURE, message='An internal server error occurred')
            
            headers = handlers.get_response_headers('1.1', request.is_secure())
            
            return response_utils.create_taxii_response(m.to_xml(), headers)

        resp = HttpResponseServerError()
        resp.body = 'A server error occurred'
        return resp