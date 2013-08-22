# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import logging
from django.http import HttpResponseServerError

import libtaxii.messages as tm
import taxii_services.handlers as handlers

class ProcessExceptionMiddleware(object):
    def process_exception(self, request, exception):
        logger = logging.getLogger('yeti.taxii_services.middleware.ProcessExceptionMiddleware.process_exception')
        logger.exception("server error occured")
    
        if request.path.startswith('/services'):
            logger.debug('returning ST_FAILURE message')
            m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_FAILURE, message='An internal server error occurred')
            return handlers.create_taxii_response(m, handlers.HTTP_STATUS_OK, use_https=request.is_secure()) # should the http status be 500?

        resp = HttpResponseServerError()
        resp.body = 'A server error occurred'
        return resp