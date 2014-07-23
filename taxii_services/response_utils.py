# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import libtaxii as t
#import libtaxii.messages_10 as tm10
#import libtaxii.messages_11 as tm11

from django.http import HttpResponse

def create_taxii_response(string_message, headers, status_code=200):
    """
    string_message - A string that will go in the HTTPResponse. Should be a serialized TAXII Message
    status_code - The status code to use. Defaults to 200
    headers - The headers to use in the response. Must be a dict. Can be a
              dict defined by response_utils or custom dict.
    """
    
    resp = HttpResponse()
    for name, value in headers.iteritems():
        resp[name] = value
    resp.content = string_message
    resp.status_code = status_code
    return resp

class HttpResponseTaxii(HttpResponse):
    """
    A Django TAXII HTTP Response. Extends the base django.http.HttpResponse 
    to allow quick and easy specification of TAXII HTTP headers.in
    """
    def __init__(self, string_message, taxii_headers, *args, **kwargs):
        #TODO: Should TAXII headers have a default? e.g., TAXII 1.1 HTTPS Headers?
        super(HttpResponse, self).__init__(*args, **kwargs)
        self.content = string_message
        for k, v in taxii_headers.iteritems():
            self[k.lower()] = v
        #for k, v in taxii_headers.iteritems():
        #    self._headers[k.lower()] = v

        
    

TAXII_11_HTTPS_Headers = {'Content-Type': 'application/xml',
                          'X-TAXII-Content-Type': t.VID_TAXII_XML_11,
                          'X-TAXII-Protocol': t.VID_TAXII_HTTPS_10,
                          'X-TAXII-Services': t.VID_TAXII_SERVICES_11}

TAXII_11_HTTP_Headers = {'Content-Type': 'application/xml',
                         'X-TAXII-Content-Type': t.VID_TAXII_XML_11,
                         'X-TAXII-Protocol': t.VID_TAXII_HTTP_10,
                         'X-TAXII-Services': t.VID_TAXII_SERVICES_11}

TAXII_10_HTTPS_Headers = {'Content-Type': 'application/xml',
                          'X-TAXII-Content-Type': t.VID_TAXII_XML_10,
                          'X-TAXII-Protocol': t.VID_TAXII_HTTPS_10,
                          'X-TAXII-Services': t.VID_TAXII_SERVICES_10}

TAXII_10_HTTP_Headers = {'Content-Type': 'application/xml',
                         'X-TAXII-Content-Type': t.VID_TAXII_XML_10,
                         'X-TAXII-Protocol': t.VID_TAXII_HTTP_10,
                         'X-TAXII-Services': t.VID_TAXII_SERVICES_10}