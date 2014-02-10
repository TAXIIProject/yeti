# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import logging
from django.http import HttpResponseServerError

import libtaxii.messages_11 as tm11
import taxii_services.handlers as handlers

class ProcessExceptionMiddleware(object):
    def process_exception(self, request, exception):
        logger = logging.getLogger('yeti.taxii_services.middleware.ProcessExceptionMiddleware.process_exception')
        logger.exception('Server error occured')
    
        if request.path.startswith('/services'):
            logger.debug('Returning ST_FAILURE message')
            m = tm11.StatusMessage(tm11.generate_message_id(), '0', status_type=tm11.ST_FAILURE, message='An internal server error occurred')
            return handlers.create_taxii_response(m, handlers.HTTP_STATUS_OK, use_https=request.is_secure())

        resp = HttpResponseServerError()
        resp.body = 'A server error occurred'
        return resp