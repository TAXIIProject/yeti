# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import logging
from django.http import HttpResponseServerError

import libtaxii.messages_11 as tm11
from taxiiweb import response_utils
import settings
import traceback

class TaxiiStatusMessageMiddleware(object):
    def process_exception(self, request, exception):
        if settings.DEBUG is False:
            message = 'An internal server error occurred'
        else:
            message = str(exception)
            print traceback.format_exc()
        
        m = tm11.StatusMessage(tm11.generate_message_id(), '0', status_type=tm11.ST_FAILURE, message=message)
        return response_utils.create_taxii_response(m.to_xml(), response_utils.TAXII_11_HTTP_Headers)