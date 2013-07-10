# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import logging
from django.http import HttpResponse
import libtaxii as t
import libtaxii.messages as tm


# A set of headers that are utilized by TAXII. These are formatted as Django's
# HttpRequest.META keys: https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.HttpRequest.REQUEST
DJANGO_HTTP_HEADER_CONTENT_TYPE         = 'CONTENT_TYPE'
DJANGO_HTTP_HEADER_ACCEPT               = 'HTTP_ACCEPT'
DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE = 'HTTP_X_TAXII_CONTENT_TYPE'
DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL     = 'HTTP_X_TAXII_PROTOCOL'
DJANGO_HTTP_HEADER_X_TAXII_ACCEPT       = 'HTTP_X_TAXII_ACCEPT'
DJANGO_HTTP_HEADER_X_TAXII_SERVICES     = 'HTTP_X_TAXII_SERVICES'

# A list of request headers that are required by TAXII
DICT_REQUIRED_TAXII_HTTP_HEADERS = (DJANGO_HTTP_HEADER_CONTENT_TYPE, 
                                    DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE,
                                    DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL)

#For each TAXII Header that may appear in a request, a list of the values this application supports
DICT_TAXII_HTTP_HEADER_VALUES = {DJANGO_HTTP_HEADER_ACCEPT: ['application/xml'],
                                 DJANGO_HTTP_HEADER_CONTENT_TYPE: ['application/xml'],
                                 DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE: [t.VID_TAXII_XML_10],
                                 DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL: [t.VID_TAXII_HTTPS_10]}

# A set of headers that are utilized by TAXII. These are formatted using HTTP header conventions
HTTP_HEADER_CONTENT_TYPE            = 'Content-Type'
HTTP_HEADER_ACCEPT                  = 'Accept'
HTTP_HEADER_X_TAXII_CONTENT_TYPE    = 'X-TAXII-Content-Type'
HTTP_HEADER_X_TAXII_PROTOCOL        = 'X-TAXII-Protocol'
HTTP_HEADER_X_TAXII_ACCEPT          = 'X-TAXII-Accept'
HTTP_HEADER_X_TAXII_SERVICES        = 'X-TAXII-Services'

# Dictionary for mapping Django's HttpRequest.META headers to actual HTTP headers
DICT_REVERSE_DJANGO_NORMALIZATION = {DJANGO_HTTP_HEADER_CONTENT_TYPE: HTTP_HEADER_CONTENT_TYPE,
                                     DJANGO_HTTP_HEADER_X_TAXII_CONTENT_TYPE: HTTP_HEADER_X_TAXII_CONTENT_TYPE,
                                     DJANGO_HTTP_HEADER_X_TAXII_PROTOCOL: HTTP_HEADER_X_TAXII_PROTOCOL,
                                     DJANGO_HTTP_HEADER_ACCEPT: HTTP_HEADER_ACCEPT}

# HTTP status codes
HTTP_STATUS_OK = 200

def create_taxii_response(message, status_code=HTTP_STATUS_OK):
    '''Creates a TAXII HTTP Response for a given message and status code'''
    resp = HttpResponse()
    resp.content = message.to_xml()
    set_taxii_headers_response(resp)
    resp.status_code = status_code
    return resp

def set_taxii_headers_response(response):
    '''Sets the TAXII HTTP Headers for a given HTTP response'''
    response[HTTP_HEADER_CONTENT_TYPE] = 'application/xml'
    response[HTTP_HEADER_X_TAXII_CONTENT_TYPE] = t.VID_TAXII_XML_10
    response[HTTP_HEADER_X_TAXII_PROTOCOL] = t.VID_TAXII_HTTPS_10
    return response

def validate_taxii_headers(request, request_message_id):
    '''
    Validates TAXII headers. It returns a response containing a TAXII
    status message if the headers were not valid. It returns None if 
    the headers are valid.
    '''
    # Make sure the required headers are present
    missing_required_headers = set(DICT_REQUIRED_TAXII_HTTP_HEADERS).difference(set(request.META))
    if missing_required_headers:
        msg = "Required headers not present: [%s]" % (', '.join([DICT_REVERSE_DJANGO_NORMALIZATION[x] for x in missing_required_headers])) 
        m = tm.StatusMessage(tm.generate_message_id(), 
                             request_message_id, 
                             status_type=tm.ST_FAILURE, 
                             message=msg)
        return create_taxii_response(m)

    #For headers that exist, make sure the values are supported
    for header in DICT_TAXII_HTTP_HEADER_VALUES:
        if header not in request.META:
            continue

        header_value = request.META[header]
        supported_values = DICT_TAXII_HTTP_HEADER_VALUES[header]
        
        if header_value not in supported_values:
            msg = 'The value of %s is not supported. The value was %s. Supported values are %s' % (DICT_REVERSE_DJANGO_NORMALIZATION[header], 
                                                                                                   header_value, 
                                                                                                   supported_values)
            
            m = tm.StatusMessage(tm.generate_message_id(),
                                 request_message_id,
                                 status_type=tm.ST_FAILURE,
                                 message=msg)
            return create_taxii_response(m)
            
        # At this point, the header values are known to be good.
        return None

def validate_taxii_request(request):
    '''Validates the broader request parameters and request type for a TAXII exchange'''
    logger = logging.getLogger("taxii_services.utils.handlers.validate_taxii_request")
    source_ip = get_source_ip(request)
    logger.info('entering service dispatcher for ip %s' % (source_ip))
    
    if request.method != 'POST':
        logger.info('Request from ip: %s was not POST. Returning error.', source_ip)
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_FAILURE, message='Request must be POST')
        return create_taxii_response(m)
    
    header_validation_resp = validate_taxii_headers(request, '0') # TODO: What to use for request message id?
    if header_validation_resp: # If response is not None an validation of the TAXII headers failed
        return header_validation_resp
    
    if len(request.body) == 0:
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_FAILURE, message='No POST data')
        logger.info('Request from ip: %s had a body length of 0. Returning error.', source_ip)
        return create_taxii_response(m)
    
    return None



def get_source_ip(request):
    '''Given a request object, returns the source IP used to make the request.'''
    if request is None: 
        return None
    
    x_header = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_header.split(',')[0] if x_header else request.META.get('REMOTE_ADDR')
    
    return ip

