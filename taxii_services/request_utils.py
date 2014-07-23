# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import libtaxii as t
import libtaxii.messages_10 as tm10
import libtaxii.messages_11 as tm11
import libtaxii.taxii_default_query as tdq

from functools import wraps
import response_utils

#1. Validate request (headers, POST) [common]
#2. Deserialize message [pretty common]
#3. Check message type [common]
#4. Create response message [uncommon]
#5. Create response (headers, etc) [common]
#6. Send to client [common]

class HeaderRule:
    PRESENCE_REQUIRED = 0
    PRESENCE_OPTIONAL = 1
    PRESENCE_PROHIBITED = 2
    
    def __init__(self, header_name, presence, value_list = None):
        self.header_name = header_name
        self.presence = presence
        self.value_list = value_list or []
        if not isinstance(self.value_list, list):
            self.value_list = [self.value_list]
    
    @staticmethod
    def evaluate_header_rules(django_request, header_rules):
        """
            django_request - a Django request
            header_rules - A list of HeaderRule objects
            
            Raises an exception is something is wrong, does nothing if nothing is wrong.
            This is intended to be used by validate_request, but doesn't have to be.
        """
        for rule in header_rules:
            header_name = rule.header_name
            request_value = django_request.META.get(header_name)
            if request_value is None and rule.presence == PRESENCE_REQUIRED:
                raise ValueError('Required header not present: %s' % header_name)
            elif request_value is not None and rule.presence == HeaderRule.PRESENCE_PROHIBITED:
                raise ValueError('Prohibited header is present: %s' % header_name)
            
            if request_value is None:
                continue
            
            if request_value not in rule.value_list:
                raise ValueError('Header value not in allowed list. Header name: %s; Allowed values: %s;' % (header_name, rule.value_list))

#Rules you can use for TAXII 1.1 Services
TAXII_11_HeaderRules = [
    HeaderRule('CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, 'application/xml'),
    HeaderRule('HTTP_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, 'application/xml'),
    HeaderRule('HTTP_X_TAXII_CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, t.VID_TAXII_XML_11),
    HeaderRule('HTTP_X_TAXII_PROTOCOL', HeaderRule.PRESENCE_REQUIRED, [t.VID_TAXII_HTTP_10, t.VID_TAXII_HTTP_10]),
    HeaderRule('HTTP_X_TAXII_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, t.VID_TAXII_XML_11),
    HeaderRule('HTTP_X_TAXII_SERVICES', HeaderRule.PRESENCE_REQUIRED, t.VID_TAXII_SERVICES_11)]

TAXII_10_HeaderRules = [
    HeaderRule('CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, 'application/xml'),
    HeaderRule('HTTP_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, 'application/xml'),
    HeaderRule('HTTP_X_TAXII_CONTENT_TYPE', HeaderRule.PRESENCE_REQUIRED, t.VID_TAXII_XML_10),
    HeaderRule('HTTP_X_TAXII_PROTOCOL', HeaderRule.PRESENCE_REQUIRED, [t.VID_TAXII_HTTP_10, t.VID_TAXII_HTTP_10]),
    HeaderRule('HTTP_X_TAXII_ACCEPT', HeaderRule.PRESENCE_OPTIONAL, t.VID_TAXII_XML_10),
    HeaderRule('HTTP_X_TAXII_SERVICES', HeaderRule.PRESENCE_REQUIRED, t.VID_TAXII_SERVICES_10)]

def validate_taxii(header_rules=TAXII_11_HeaderRules, message_types = None, do_validate = True):
    #print "hr", header_rules
    #print "mts", message_types
    #print "dv", do_validate
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            ### Begin Picking Response Headers
            response_headers = {'Content-Type': 'application/xml'}
            x_taxii_content_type = request.META.get('HTTP_X_TAXII_CONTENT_TYPE', None)
            #TODO: Choose this first based on the X-TAXII-Accept header value and only use
            #      the Content-Type as a fallback.
            if x_taxii_content_type == t.VID_TAXII_XML_10:#Use TAXII 1.0 if we know its supported
                sm = tm10.StatusMessage
                response_headers['X-TAXII-Content-Type'] = t.VID_TAXII_XML_10
                response_headers['X-TAXII-Services'] = t.VID_TAXII_SERVICES_10
            else:#Use TAXII 1.1 by default
                sm = tm11.StatusMessage
                response_headers['X-TAXII-Content-Type'] = t.VID_TAXII_XML_11
                response_headers['X-TAXII-Services'] = t.VID_TAXII_SERVICES_11
            
            if request.is_secure():
                response_headers['X-TAXII-Protocol'] = t.VID_TAXII_HTTPS_10
            else:
                response_headers['X-TAXII-Protocol'] = t.VID_TAXII_HTTP_10
            ### End Picking Response Headers
            
            #Evaluate Header Rules
            try:
                HeaderRule.evaluate_header_rules(request, header_rules)
            except ValueError as e:
                msg = sm.StatusMessage(generate_message_id, '0', status_type='BAD_MESSAGE', message=e.message)
                return response_utils.HttpResponseTaxii(msg.to_xml(), response_headers)
            
            if request.method != 'POST':
                msg = sm.StatusMessage(generate_message_id, '0', status_type='BAD_MESSAGE', message='Request method was not POST')
                return response_utils.HttpResponseTaxii(msg.to_xml(), response_headers)
            
            #If requested, attempt to validate
            if do_validate:
                try:
                    validate(request)
                except Exception as e:
                    msg = sm.StatusMessage(generate_message_id, '0', status_type='BAD_MESSAGE', message=e.message)
                    return response_utils.HttpResponseTaxii(msg.to_xml(), response_headers)
            
            #Attempt to deserialize
            try:
                message = deserialize(request)
            except Exception as e:
                msg = sm.StatusMessage(generate_message_id, '0', status_type='FAILURE', message=e.message)
                return response_utils.HttpResponseTaxii(msg.to_xml(), response_headers)
            
            try:
                if message_types is None:
                    pass#No checking was requested
                elif isinstance(message_types, list):
                    if message.__class__ not in message_types:
                        raise ValueError('Message type not allowed. Must be one of: %s' % message_types)
                elif isinstance(message_types, object):
                    if not isinstance(message, message_types):
                        raise ValueError('Message type not allowed. Must be: %s' % message_types)
                elif message_types is not None:
                    raise ValueError('Something strange happened with message_types! Was not a list or object!')
            except ValueError as e:
                msg = sm.StatusMessage(generate_message_id, message.message_id, status_type='FAILURE', message=e.message)
                return response_utils.HttpResponseTaxii(msg.to_xml(), response_headers)
            
            kwargs['taxii_message'] = message
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

    #TODO: This is older and is superseded by the decorator. Consider removing this.
# def validate_and_parse_request(django_request, header_rules, message_types = None, do_validate = True):
    # """
    # django_request - a Django HTTP Request from the user agent
    # header_rules - a list of HeaderRule objects to be evaluated
    # message_types - a list of allowed message types, 
                    # a string with one allowed message type, 
                    # or None (no check will be done)
    # do_validate - a boolean (True/False) indicating whether the request.body 
               # should be validated against known validators. An 
               # exception will be thrown if a validator is not found.
    
    # This function does the following:
    # 1. Evaluates the supplied header rules against the Django request
       # and raises an Exception if a rule is violated
    # 2. Checks to see if the method is POST (all TAXII requests are post)
       # Raises an Exception if the method is not POST
    # 3. Deserializes the message.
    # 4. If message_types is not None, check to see if the message.message_type
       # property is in the supplied list (or matches the supplied string)
    # """
    
    # HeaderRule.evaluate_header_rules(django_request, header_rules)
    
    # if django_request.method != 'POST':
        # raise Exception('Request method was not POST')
    
    # if do_validate:
        # validate(django_request)
        
    # message = deserialize(django_request)
    
    # if isinstance(message_types, list):
        # if message.__class__ not in message_types:
            # raise Exception('Message type not allowed. Must be one of: %s' % message_types)
    # elif isinstance(message_types, object):
        # if not isinstance(message, message_types):
            # raise Exception('Message type not allowed. Must be: %s' % message_types)
    # elif message_types is not None:
        # raise Exception('Something strange happened with message_types! Was not a list or object!')
    
    # return message

def deserialize(django_request):
    """
    django_request - A django request that contains a TAXII Message to deserialize
    
    Looks at the TAXII Headers to determine what the TAXII Message _should_ be,
    and looks for a registered deserializer that can deserialize the TAXII Message.
    
    To register a deserializer, see register_deserializer.
    """
    content_type = django_request.META['CONTENT_TYPE']
    x_taxii_content_type = django_request.META['HTTP_X_TAXII_CONTENT_TYPE']
    
    deserializer_key = _get_deserializer_key(content_type, x_taxii_content_type)
    deserializer = deserializers.get(deserializer_key)
    if deserializer is None:
        raise Exception('Deserializer not found!')
    
    return deserializer(django_request.body)

def validate(django_request):
    """
    django_request - A django request that contains a TAXII Message to validate
    
    Looks at the TAXII Headers to determine what the TAXII Message _should_ be,
    and looks for a registered validator that can validate the TAXII Message.
    
    To register a validator, see register_deserializer.
    """
    content_type = django_request.META['CONTENT_TYPE']
    x_taxii_content_type = django_request.META['HTTP_X_TAXII_CONTENT_TYPE']
    
    deserializer_key = _get_deserializer_key(content_type, x_taxii_content_type)
    validator = validators.get(deserializer_key)
    if validator is None:
        raise Exception('Validator not found!')
    
    return validator(django_request.body)

def _get_deserializer_key(content_type, x_taxii_content_type):
    """
    Internal use only.
    """
    return content_type + x_taxii_content_type

deserializers = {}
validators = {}
def register_deserializer(content_type, x_taxii_content_type, deserialize_function, validate_function = None):
    """
    Registers a deserializer for use. 
    content_type - The Content-Type HTTP header value that this deserializer is used for
    x_taxii_content_type - The X-TAXII-Content-Type HTTP header value that this deserializer is used for
    deserialize_function - The deserializer function to be used for the specific content_type and x_taxii_content_type
    validate_function - The validation function to be used for the specific content_type and x_taxii_content_type. Can be None.
                        The validate_function must take a single string argument (representing the request.body) only.
    """
    deserializer_key = _get_deserializer_key(content_type, x_taxii_content_type)
    deserializers[deserializer_key] = deserialize_function
    validators[deserializer_key] = validate_function

#A TAXII XML 1.1 and XML 1.0 Deserializer (libtaxii) is registered by default
register_deserializer('application/xml', t.VID_TAXII_XML_11, tm11.get_message_from_xml, tm11.validate_xml)
register_deserializer('application/xml', t.VID_TAXII_XML_10, tm10.get_message_from_xml, tm10.validate_xml)

def deregister_deserializer(content_type, x_taxii_content_type):
    """
    """
    deserializer_key = _get_deserializer_key(content_type, x_taxii_content_type)
    del deserializers[deserializer_key]

