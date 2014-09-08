# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import libtaxii as t
import libtaxii.messages_10 as tm10
import libtaxii.messages_11 as tm11
import libtaxii.taxii_default_query as tdq
import libtaxii.clients as tc
from libtaxii.constants import *
from libtaxii.common import generate_message_id

#from taxii_services.handlers import (TAXII_11_HTTPS_Headers, TAXII_11_HTTP_Headers, TAXII_10_HTTPS_Headers, TAXII_10_HTTP_Headers, get_headers)

from datetime import datetime, timedelta
from dateutil.tz import tzutc
from taxii_services import models
from django.core.management import call_command

from django.test import TestCase, Client
from copy import deepcopy
import urllib2

# Global params for TestCases to use
DEBUG = True
#HOST = 'localhost'
#PORT = 8080

#PROXY_TYPE = tc.HttpClient.PROXY_HTTP
#PROXY_ADDR = "http://gatekeeper.mitre.org:80"
#PROXY_ADDR = None

INBOX_11_PATH = '/services/inbox/'
DISCOVERY_11_PATH = '/services/discovery/'
POLL_11_PATH = '/services/poll/'
COLLECTION_MGMT_11_PATH = '/services/collection-management/'

INBOX_10_PATH = '/services/inbox/'
DISCOVERY_10_PATH = '/services/discovery/'
POLL_10_PATH = '/services/poll/'
FEED_MGMT_10_PATH = '/services/collection-management/'

stix_watchlist_111 = '''
<stix:STIX_Package
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:stix="http://stix.mitre.org/stix-1"
    xmlns:indicator="http://stix.mitre.org/Indicator-2"
    xmlns:cybox="http://cybox.mitre.org/cybox-2"
    xmlns:DomainNameObj="http://cybox.mitre.org/objects#DomainNameObject-1"
    xmlns:cyboxVocabs="http://cybox.mitre.org/default_vocabularies-2"
    xmlns:stixVocabs="http://stix.mitre.org/default_vocabularies-1"
    xmlns:example="http://example.com/"
    xsi:schemaLocation=
    "http://stix.mitre.org/stix-1 ../stix_core.xsd
    http://stix.mitre.org/Indicator-2 ../indicator.xsd
    http://cybox.mitre.org/default_vocabularies-2 ../cybox/cybox_default_vocabularies.xsd
    http://stix.mitre.org/default_vocabularies-1 ../stix_default_vocabularies.xsd
    http://cybox.mitre.org/objects#DomainNameObject-1 ../cybox/objects/Domain_Name_Object.xsd"
    id="example:STIXPackage-f61cd874-494d-4194-a3e6-6b487dbb6d6e"
    timestamp="2014-05-08T09:00:00.000000Z"
    version="1.1.1"
    >
    <stix:STIX_Header>
        <stix:Title>Example watchlist that contains domain information.</stix:Title>
        <stix:Package_Intent xsi:type="stixVocabs:PackageIntentVocab-1.0">Indicators - Watchlist</stix:Package_Intent>
    </stix:STIX_Header>
    <stix:Indicators>
        <stix:Indicator xsi:type="indicator:IndicatorType" id="example:Indicator-2e20c5b2-56fa-46cd-9662-8f199c69d2c9" timestamp="2014-05-08T09:00:00.000000Z">
            <indicator:Type xsi:type="stixVocabs:IndicatorTypeVocab-1.1">Domain Watchlist</indicator:Type>
            <indicator:Description>Sample domain Indicator for this watchlist</indicator:Description>
            <indicator:Observable id="example:Observable-87c9a5bb-d005-4b3e-8081-99f720fad62b">
                <cybox:Object id="example:Object-12c760ba-cd2c-4f5d-a37d-18212eac7928">
                    <cybox:Properties xsi:type="DomainNameObj:DomainNameObjectType" type="FQDN">
                        <DomainNameObj:Value condition="Equals" apply_condition="ANY">malicious1.example.com##comma##malicious2.example.com##comma##malicious3.example.com</DomainNameObj:Value>
                    </cybox:Properties>
                </cybox:Object>
            </indicator:Observable>
        </stix:Indicator>
    </stix:Indicators>
</stix:STIX_Package>'''

stix_watchlist_10 = '''
<stix:STIX_Package
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:stix="http://stix.mitre.org/stix-1"
    xmlns:indicator="http://stix.mitre.org/Indicator-2"
    xmlns:cybox="http://cybox.mitre.org/cybox-2"
    xmlns:URIObject="http://cybox.mitre.org/objects#URIObject-2"
    xmlns:cyboxVocabs="http://cybox.mitre.org/default_vocabularies-2"
    xmlns:stixVocabs="http://stix.mitre.org/default_vocabularies-1"
    xmlns:example="http://example.com/"
    xsi:schemaLocation=
    "http://stix.mitre.org/stix-1 http://stix.mitre.org/XMLSchema/core/1.0/stix_core.xsd
    http://stix.mitre.org/Indicator-2 http://stix.mitre.org/XMLSchema/indicator/2.0/indicator.xsd
    http://cybox.mitre.org/default_vocabularies-2 http://cybox.mitre.org/XMLSchema/default_vocabularies/2.0.0/cybox_default_vocabularies.xsd
    http://stix.mitre.org/default_vocabularies-1 http://stix.mitre.org/XMLSchema/default_vocabularies/1.0.0/stix_default_vocabularies.xsd
    http://cybox.mitre.org/objects#URIObject-2 http://cybox.mitre.org/XMLSchema/objects/URI/2.0/URI_Object.xsd"
    id="example:STIXPackage-f61cd874-494d-4194-a3e6-6b487dbb6d6e"
    version="1.0">
    <stix:STIX_Header>
        <stix:Title>Example watchlist that contains domain information.</stix:Title>
        <stix:Package_Intent xsi:type="stixVocabs:PackageIntentVocab-1.0">Indicators - Watchlist</stix:Package_Intent>
    </stix:STIX_Header>
    <stix:Indicators>
        <stix:Indicator xsi:type="indicator:IndicatorType" id="example:Indicator-2e20c5b2-56fa-46cd-9662-8f199c69d2c9">
            <indicator:Type xsi:type="stixVocabs:IndicatorTypeVocab-1.0">Domain Watchlist</indicator:Type>
            <indicator:Description>Sample domain Indicator for this watchlist</indicator:Description>
            <indicator:Observable id="example:Observable-87c9a5bb-d005-4b3e-8081-99f720fad62b">
                <cybox:Object id="example:Object-12c760ba-cd2c-4f5d-a37d-18212eac7928">
                    <cybox:Properties xsi:type="URIObject:URIObjectType">
                        <URIObject:Value condition="Equals" apply_condition="ANY">malicious1.example.com,malicious2.example.com,malicious3.example.com,</URIObject:Value>
                    </cybox:Properties>
                </cybox:Object>
            </indicator:Observable>
        </stix:Indicator>
    </stix:Indicators>
</stix:STIX_Package>'''
    
def get_message_from_client_response(resp, in_response_to):
    """ helper func"""
    
    taxii_content_type = resp.get('X-TAXII-Content-Type', None)
    response_message = resp.content

    if taxii_content_type is None:
        m = str(resp) + '\r\n' + response_message
        return tm11.StatusMessage(message_id='0', in_response_to=in_response_to, status_type=ST_FAILURE, message=m)
    elif taxii_content_type == VID_TAXII_XML_10:  # It's a TAXII XML 1.0 message
        return tm10.get_message_from_xml(response_message)
    elif taxii_content_type == VID_TAXII_XML_11:  # It's a TAXII XML 1.1 message
        return tm11.get_message_from_xml(response_message)
    elif taxii_content_type == VID_CERT_EU_JSON_10:
        return tm10.get_message_from_json(response_message)
    else:
        raise ValueError('Unsupported X-TAXII-Content-Type: %s' % taxii_content_type)

    return None


def make_request(path='/', post_data=None, header_dict=None, response_msg_type=None, st=None, sd_keys=None, expected_code=200):
    c = Client()
        
    if not header_dict:
        # Use TAXII 1.1 HTTP Headers
        header_dict = get_headers(VID_TAXII_SERVICES_11, is_secure=False)
        header_dict['Accept'] = 'application/xml'
        header_dict['X-TAXII-Accept'] = VID_TAXII_XML_11
    
    
    if post_data: # Make a POST
        resp = c.post(path, data=post_data, content_type='application_xml', **header_dict)
    else: # Make a GET
        resp = c.get(path, **header_dict)
    
    if resp.status_code != expected_code:
        msg = resp.content
        raise ValueError("Response code was not %s. Was: %s.\r\n%s" % \
                         (str(expected_code), str(resp.status_code), msg) )
    
    msg = get_message_from_client_response(resp, '0')
    
    if (  response_msg_type and 
         msg.message_type != response_msg_type ):
        raise ValueError("Incorrect message type sent in response. Expected: %s. Got: %s.\r\n%s" % \
                         (response_msg_type, msg.message_type, msg.to_xml(pretty_print=True)) )
    
    if st:
        if msg.status_type != st:
            raise ValueError("Incorrect status type. Expected %s got %s)\r\n%s" % \
                             (st, msg.status_type, msg.to_xml(pretty_print=True))  )
    
    if sd_keys:
        for key in sd_keys:
            if key not in msg.status_detail:
                raise ValueError("SD Key not present: %s\r\n%s" % \
                                 (key, msg.to_xml(pretty_print=True))  )
    
    return msg

# Requests that come through via the test harness
# don't have their headers normalized by Django.
# This means I can't reuse application code from elsewhere. Grrr.

TAXII_11_HTTPS_Headers = {'CONTENT_TYPE': 'application/xml',
                          'HTTP_X_TAXII_CONTENT_TYPE': VID_TAXII_XML_11,
                          'HTTP_X_TAXII_PROTOCOL': VID_TAXII_HTTPS_10,
                          'HTTP_X_TAXII_SERVICES': VID_TAXII_SERVICES_11,
                          'HTTP_ACCEPT': 'application/xml',
                          'HTTP_X_TAXII_ACCEPT': VID_TAXII_XML_11}

TAXII_11_HTTP_Headers = {'CONTENT_TYPE': 'application/xml',
                         'HTTP_X_TAXII_CONTENT_TYPE': VID_TAXII_XML_11,
                         'HTTP_X_TAXII_PROTOCOL': VID_TAXII_HTTP_10,
                         'HTTP_X_TAXII_SERVICES': VID_TAXII_SERVICES_11,
                          'HTTP_ACCEPT': 'application/xml',
                          'HTTP_X_TAXII_ACCEPT': VID_TAXII_XML_11}

TAXII_10_HTTPS_Headers = {'CONTENT_TYPE': 'application/xml',
                          'HTTP_X_TAXII_CONTENT_TYPE': VID_TAXII_XML_10,
                          'HTTP_X_TAXII_PROTOCOL': VID_TAXII_HTTPS_10,
                          'HTTP_X_TAXII_SERVICES': VID_TAXII_SERVICES_10,
                          'HTTP_ACCEPT': 'application/xml',
                          'HTTP_X_TAXII_ACCEPT': VID_TAXII_XML_10}

TAXII_10_HTTP_Headers = {'CONTENT_TYPE': 'application/xml',
                         'HTTP_X_TAXII_CONTENT_TYPE': VID_TAXII_XML_10,
                         'HTTP_X_TAXII_PROTOCOL': VID_TAXII_HTTP_10,
                         'HTTP_X_TAXII_SERVICES': VID_TAXII_SERVICES_10,
                          'HTTP_ACCEPT': 'application/xml',
                          'HTTP_X_TAXII_ACCEPT': VID_TAXII_XML_10}

def get_headers(taxii_services_version, is_secure):
    """
    Convenience method for selecting headers
    """
    if taxii_services_version == VID_TAXII_SERVICES_11 and is_secure:
        return deepcopy(TAXII_11_HTTPS_Headers)
    elif taxii_services_version == VID_TAXII_SERVICES_11 and not is_secure:
        return deepcopy(TAXII_11_HTTP_Headers)
    elif taxii_services_version == VID_TAXII_SERVICES_10 and is_secure:
        return deepcopy(TAXII_10_HTTPS_Headers)
    elif taxii_services_version == VID_TAXII_SERVICES_10 and not is_secure:
        return deepcopy(TAXII_10_HTTP_Headers)
    else:
        raise ValueError("Unknown combination for taxii_services_version and is_secure!")


class ProtocolTests(TestCase):
    """
    Tests the implementation of the protocol side,
    making sure failure scenarios fail and
    success cases succeed.
    """
    
    fixtures = ['test_data.json']
    
    def test_01(self):
        """
        Sends an Inbox Message to an invalid URL. 
        Should get back a 404
        """
        inbox_message = tm11.InboxMessage(generate_message_id())
        msg = make_request(post_data = inbox_message.to_xml(), path='/Services/PathThatShouldNotWork/', expected_code = 404)
        #msg = self.base_test(post_data = inbox_message.to_xml(), path='/Services/PathThatShouldNotWork/', expected_code = 404)
    
    def test_02(self):
        """
        Tests sending a GET request to the server. Should result in a BAD MESSAGE
        """
        # Lack of post_data makes it a GET request
        msg = make_request(path=DISCOVERY_11_PATH)
        #msg = self.base_test(path=DISCOVERY_11_PATH)
    
    def test_03(self):
        """
        Send an XML fragment to the server
        """
        msg = make_request(path=DISCOVERY_11_PATH, post_data='<XML_that_is_not_well_formed>', response_msg_type=MSG_STATUS_MESSAGE)
        #msg = self.base_test(path=DISCOVERY_11_PATH, post_data='<XML_that_is_not_well_formed>', response_msg_type=MSG_STATUS_MESSAGE)
    
    def test_04(self):
        """
        Send schema-invalid XML
        """
        msg = make_request(path=DISCOVERY_11_PATH, post_data='<well_formed_schema_invalid_xml/>', response_msg_type=MSG_STATUS_MESSAGE)
        #msg = self.base_test(path=DISCOVERY_11_PATH, post_data='<well_formed_schema_invalid_xml/>', response_msg_type=MSG_STATUS_MESSAGE)
    
    # The next few tests test headers presence/absence
    # and unsupported values
    
    def test_05(self):
        """
        For each set of TAXII Headers, test the following:
        - One header missing
        - A bad value for each header
        - Other permutations in the future?
        """
        
        #TODO: The responses could probably be checked better
        #TODO: This whole thing can probably be done better,
        #      but it's probably sufficient for now
        
        #Tuples of services version / is_secure
        HTTP = False
        HTTPS = True
        tuples = (  (VID_TAXII_SERVICES_11, HTTPS),
                    (VID_TAXII_SERVICES_11, HTTP),
                    (VID_TAXII_SERVICES_10, HTTPS),
                    (VID_TAXII_SERVICES_10, HTTP)
                  )
        
        # Create a list of headers for mangling header values
        tmp_headers = get_headers(  tuples[0][0], tuples[0][1]  )
        header_list = tmp_headers.keys()
        
        # Iterate over every TAXII Service version / is_secure value,
        # over every header, and try that header with a bad value
        # and not present
        for tuple in tuples:
            if tuple[0] == VID_TAXII_SERVICES_11:
                disc_req_xml = tm11.DiscoveryRequest(generate_message_id()).to_xml()
            else:
                disc_req_xml = tm10.DiscoveryRequest(generate_message_id()).to_xml()
            for header in header_list:
                expected_code = 200 if header != 'HTTP_ACCEPT' else 406
                r_msg = MSG_STATUS_MESSAGE
                request_headers = get_headers(tuple[0], tuple[1])
                
                # Try the bad header value
                request_headers[header] = 'THIS_IS_A_BAD_VALUE'
                #print header, request_headers[header]
                msg = make_request(post_data = disc_req_xml, 
                                     path=DISCOVERY_11_PATH, 
                                     response_msg_type = r_msg, 
                                     header_dict=request_headers,
                                     expected_code = expected_code)
                #print msg.to_xml(pretty_print=True)
                
                # Now try without the header
                if header in ('HTTP_ACCEPT', 'HTTP_X_TAXII_ACCEPT'): # These headers, if missing, should result an a valid response being sent
                    expected_code = 200
                    r_msg = MSG_DISCOVERY_RESPONSE
                del request_headers[header]
                msg =  make_request(post_data = disc_req_xml, 
                                     path=DISCOVERY_11_PATH, 
                                     response_msg_type = r_msg, 
                                     header_dict=request_headers, 
                                     expected_code = expected_code)
                #print msg.to_xml(pretty_print=True)
                # Good, now on to the next one!
        pass
    
    def test_06(self):
        """
        Send a discovery message mismatched with the message binding ID
        """
        # TODO: Write this
        pass
    
    def test_07(self):
        """
        Send a request mismatched with the protocol binding ID
        """
        # TODO: Write this
        pass
    
    def test_08(self):
        """
        Send a request mismatched with the services version
        """
        # TODO: Write this
        pass
    
    def test_09(self):
        """
        Send a TAXII 1.0 message with an X-TAXII-Accept value of TAXII 1.1
        """
        # TODO: Write this
        pass
    
    def test_10(self):
        """
        Send a TAXII 1.1 message with an X-TAXII-Accept value of TAXII 1.0
        """
        # TODO: Write this
        pass

class InboxTests(TestCase):
    """
    Test various aspects of the
    taxii_handlers.InboxMessage11Handler
    """
    
    # These tests expect the following objects in the database:
    # /services/test_inbox_1/ - TAXII 1.1 Inbox Service, accepts all content, enabled, dcns = required (default)
    # /services/test_inbox_2/ - TAXII 1.1 Inbox Service, accepts all content, enabled, dcns = optional (default)
    # /services/test_inbox_3/ - TAXII 1.1 Inbox Service, accepts all content, enabled, dcns = prohibited 
    # TODO: Write more involved tests
    
    #fixtures = ['inbox_test_fixture.json']
    fixtures = ['test_data.json']
    
    def test_01(self):
        """
        Send a message to test_inbox_1 with a valid destination collection name
        """
        inbox = tm11.InboxMessage(generate_message_id(), destination_collection_names=['default'])
        msg = make_request('/services/test_inbox_1/', inbox.to_xml(), get_headers(VID_TAXII_SERVICES_11, False), MSG_STATUS_MESSAGE, ST_SUCCESS)
        #msg = self.send_inbox_message('/services/test_inbox_1/', VID_TAXII_XML_11, inbox)
    
    def test_02(self):
        """
        Send a message to test_inbox_1 with an invalid destination collection name
        """
        inbox = tm11.InboxMessage(generate_message_id(), destination_collection_names=['default_INVALID'])
        msg = make_request('/services/test_inbox_1/', inbox.to_xml(), get_headers(VID_TAXII_SERVICES_11, False), MSG_STATUS_MESSAGE, ST_NOT_FOUND, sd_keys=[SD_ITEM])
        #msg = self.send_inbox_message('/services/test_inbox_1/', VID_TAXII_XML_11, inbox, st=ST_NOT_FOUND, sd_keys=[SD_ITEM])
    
    def test_03(self):
        """
        Send a message to test_inbox_1 without a destination collection name
        """
        inbox = tm11.InboxMessage(generate_message_id())
        msg = make_request('/services/test_inbox_1/', 
                              inbox.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_DESTINATION_COLLECTION_ERROR, 
                              sd_keys=[SD_ACCEPTABLE_DESTINATION])
        #msg = self.send_inbox_message('/services/test_inbox_1/', VID_TAXII_XML_11, inbox, st=ST_DESTINATION_COLLECTION_ERROR, sd_keys=[SD_ACCEPTABLE_DESTINATION])
    
    def test_04(self):
        """
        Send a message to test_inbox_2 with a valid destination collection name
        """
        inbox = tm11.InboxMessage(generate_message_id(), destination_collection_names=['default'])
        msg = make_request('/services/test_inbox_2/', 
                              inbox.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_SUCCESS)
        #msg = self.send_inbox_message('/services/test_inbox_2/', VID_TAXII_XML_11, inbox)
    
    def test_05(self):
        """
        Send a message to test_inbox_2 with an invalid destination collection name
        """
        inbox = tm11.InboxMessage(generate_message_id(), destination_collection_names=['default_INVALID'])
        msg = make_request('/services/test_inbox_2/',
                              inbox.to_xml(),
                              get_headers(VID_TAXII_SERVICES_11, False),
                              MSG_STATUS_MESSAGE,
                              st=ST_NOT_FOUND,
                              sd_keys=[SD_ITEM])
        #msg = self.send_inbox_message('/services/test_inbox_2/', VID_TAXII_XML_11, inbox, st=ST_NOT_FOUND, sd_keys=[SD_ITEM])
    
    def test_06(self):
        """
        Send a message to test_inbox_2 without a destination collection name
        """
        inbox = tm11.InboxMessage(generate_message_id())
        msg = make_request('/services/test_inbox_2/', 
                              inbox.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_SUCCESS)
        #msg = self.send_inbox_message('/services/test_inbox_2/', VID_TAXII_XML_11, inbox, st=ST_SUCCESS)
    
    def test_08(self):
        """
        Send a message to test_inbox_3 with a destination collection name
        """
        inbox = tm11.InboxMessage(generate_message_id(), destination_collection_names=['default'])
        msg = make_request('/services/test_inbox_3/', 
                              inbox.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_DESTINATION_COLLECTION_ERROR)
        #msg = self.send_inbox_message('/services/test_inbox_3/', VID_TAXII_XML_11, inbox, st=ST_DESTINATION_COLLECTION_ERROR)
    
    def test_09(self):
        """
        Send a message to test_inbox_3 without a destination collection name
        """
        inbox = tm11.InboxMessage(generate_message_id())
        msg = make_request('/services/test_inbox_3/', 
                              inbox.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_SUCCESS)
        #msg = self.send_inbox_message('/services/test_inbox_3/', VID_TAXII_XML_11, inbox)
    
    def test_10(self):
        """
        Send an Inbox message with a Record Count
        """
        inbox = tm11.InboxMessage(generate_message_id(), destination_collection_names=['default'])
        inbox.record_count = tm11.RecordCount(0, True)
        msg = make_request('/services/test_inbox_1/', 
                              inbox.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_SUCCESS)
        #msg = self.send_inbox_message('/services/test_inbox_1/', VID_TAXII_XML_11, inbox)
    
    def test_11(self):
        """
        Send a TAXII 1.0 Inbox Message to /services/test_inbox_1/. Will always
        fail because /services/test_inbox_1/ requires a DCN and TAXII 1.0 cannot specify that.
        """
        inbox = tm10.InboxMessage(generate_message_id())
        msg = make_request('/services/test_inbox_1/', 
                              inbox.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_10, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_FAILURE)
        #msg = self.send_inbox_message('/services/test_inbox_1/', VID_TAXII_XML_10, inbox)
    
    def test_12(self):
        """
        Send a TAXII 1.0 Inbox Message to /services/test_inbox_2/
        """
        inbox = tm10.InboxMessage(generate_message_id())
        msg = make_request('/services/test_inbox_2/', 
                              inbox.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_10, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_SUCCESS)
        #msg = self.send_inbox_message('/services/test_inbox_2/', VID_TAXII_XML_10, inbox)
    
    def test_13(self):
        """
        Send a TAXII 1.0 Inbox Message to /services/test_inbox_3/
        """
        inbox = tm10.InboxMessage(generate_message_id())
        msg = make_request('/services/test_inbox_3/', 
                              inbox.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_10, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_SUCCESS)
        #msg = self.send_inbox_message('/services/test_inbox_3/', VID_TAXII_XML_10, inbox)

class PollRequestTests11(TestCase):

    fixtures = ['test_data.json']
    
    # Make sure query tests are in here
    
    # These tests expect the following objects in the database:
    # /services/test_poll_1/ - (Collection: Default), max_result_size = 5; requires=Subscription = False
    
    def send_poll_request(self, path, messages_vid, poll_request, status_type=None, sd_keys=None):
        #status_type=None means expect a PollResponse
        #status_type=<value> means expect a StatusMessage
        if messages_vid not in (VID_TAXII_XML_11, VID_TAXII_XML_10):
            raise ValueError("Wrong messages_vid!")
        
        client = tc.HttpClient()
        client.setProxy(tc.HttpClient.NO_PROXY)
        resp = client.callTaxiiService2(HOST, path, messages_vid, poll_request.to_xml(), PORT)
        msg = t.get_message_from_http_response(resp, poll_request.message_id)
        
        if not status_type: # Expect a Poll Response
            if msg.message_type != MSG_POLL_RESPONSE:
                raise ValueError('Expected Poll Response. Got: %s.\r\n%s' % \
                                 (msg.message_type, msg.to_xml(pretty_print=True)) )
        else: # Expect a Status Message
            if msg.message_type != MSG_STATUS_MESSAGE:
                raise ValueError('Expected Status Message. Got: %s.\r\n%s' % \
                                 (msg.message_type, msg.to_xml(pretty_print=True)) )
            if sd_keys:
                for key in sd_keys:
                    if key not in msg.status_detail:
                        raise ValueError('Expected status detail key was not present: %s\r\n%s' % \
                                         (key, msg.to_xml(pretty_print=True)) )
        return msg
    
    def test_01(self):
        """
        Test an invalid collection name
        """
        pp = tm11.PollParameters()
        pr = tm11.PollRequest(
                message_id = generate_message_id(),
                collection_name = 'INVALID_COLLECTION_NAME_13820198320',
                poll_parameters = pp)
        
        msg = make_request('/services/test_poll_1/', 
                              pr.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_NOT_FOUND,
                              sd_keys=[SD_ITEM])
        #msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr, status_type=ST_NOT_FOUND, sd_keys=[SD_ITEM])
    
    def test_02(self):
        """
        Test a begin TS later than an end TS.
        """
        begin_ts = datetime.now(tzutc())
        end_ts = begin_ts - timedelta(days=-7)
        
        pp = tm11.PollParameters()
        pr = tm11.PollRequest(
                message_id = generate_message_id(),
                collection_name = 'default',
                poll_parameters = pp,
                exclusive_begin_timestamp_label = begin_ts,
                inclusive_end_timestamp_label = end_ts)
        msg = make_request('/services/test_poll_1/', 
                              pr.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              ST_FAILURE)
        #msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr, status_type=ST_FAILURE)
    
    def test_03(self):
        """
        Test an invalid subscription ID
        """
        pr = tm11.PollRequest(
                message_id = generate_message_id(),
                collection_name = 'default',
                subscription_id = 'jdslkajdlksajdlksajld')
        msg = make_request('/services/test_poll_1/', 
                              pr.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_NOT_FOUND,
                              sd_keys=[SD_ITEM])
        #msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr, status_type=ST_NOT_FOUND, sd_keys=[SD_ITEM])
    
    def test_04(self):
        """
        Test a Content Binding ID not supported by the server
        """
        pp = tm11.PollParameters(content_bindings=[tm11.ContentBinding('some_random_binding')])
        pr = tm11.PollRequest(
                message_id = generate_message_id(),
                collection_name = 'default',
                poll_parameters = pp)
        msg = make_request('/services/test_poll_1/', 
                              pr.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_UNSUPPORTED_CONTENT_BINDING,
                              sd_keys=[SD_SUPPORTED_CONTENT])
        #msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr, status_type=ST_UNSUPPORTED_CONTENT_BINDING, sd_keys=[SD_SUPPORTED_CONTENT])
    
    def test_05(self):
        """
        Test a supported Content Binding ID with an unsupported subtype
        """
        pp = tm11.PollParameters(content_bindings=[tm11.ContentBinding(CB_STIX_XML_111, subtype_ids=['FakeSubtype'])])
        pr = tm11.PollRequest(
                message_id = generate_message_id(),
                collection_name = 'default',
                poll_parameters = pp)
        msg = make_request('/services/test_poll_1/', 
                              pr.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_STATUS_MESSAGE, 
                              st=ST_UNSUPPORTED_CONTENT_BINDING,
                              sd_keys=[SD_SUPPORTED_CONTENT])
        #msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr, status_type=ST_UNSUPPORTED_CONTENT_BINDING, sd_keys=[SD_SUPPORTED_CONTENT])

    # This test case currently fails and will not be able to pass until either django-taxii-services changes or libtaxii changes.
    # def test_06(self):
        # """
        # Test an unsupported query format
        # """
        # pp = tm11.PollParameters(query=tm11.Query(format_id='unsupported_format_id'))
        # pr = tm11.PollRequest(
                # message_id = generate_message_id(),
                # collection_name = 'default',
                # poll_parameters = pp)
        # msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr, status_type=ST_UNSUPPORTED_QUERY, sd_keys=[SD_SUPPORTED_QUERY])
    
    # This test won't be valid until Delivery Params are implemented
    # def test_07(self):
        # """
        # Test unsupported delivery parameters - protocol
        # """
        # dp = tm11.DeliveryParameters('protocol_x', 'http://example.com/whatever/', VID_TAXII_XML_11)
        # pp = tm11.PollParameters(delivery_parameters=dp)
        # pr = tm11.PollRequest(
                # message_id = generate_message_id(),
                # collection_name = 'default',
                # poll_parameters = pp)
        # msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr, status_type=ST_UNSUPPORTED_PROTOCOL, sd_keys=[SD_SUPPORTED_PROTOCOL])
    
    # This test won't be valid until Delivery Params are implemented
    # def test_08(self):
        # """
        # Test unsupported delivery parameters - message_binding
        # """
        # dp = tm11.DeliveryParameters(VID_TAXII_HTTPS_11, 'http://example.com/whatever/', 'message_binding_x')
        # pp = tm11.PollParameters(delivery_parameters=dp)
        # pr = tm11.PollRequest(
                # message_id = generate_message_id(),
                # collection_name = 'default',
                # poll_parameters = pp)
        # msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr, status_tpe=ST_UNSUPPORTED_MESSAGE, sd_keys=[SD_SUPPORTED_MESSAGE])
        
    
    def test_09(self):
        """
        Tests that a single PollRequest succeeds.
        """
        pp = tm11.PollParameters()
        pr = tm11.PollRequest(
                message_id=generate_message_id(),
                collection_name='default',
                poll_parameters=pp)
        msg = make_request('/services/test_poll_1/', 
                              pr.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_POLL_RESPONSE)
        #msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr)
        if len(msg.content_blocks) != 5:
            raise ValueError('Got %s CBs' % len(msg.content_blocks))
    
    
    def test_10(self):
        """
        Test a query. Should match just the APT1 report.
        """
        test = tdq.Test(capability_id = tdq.CM_CORE, relationship=R_EQUALS, parameters={P_VALUE: 'Unit 61398', P_MATCH_TYPE: 'case_sensitive_string'} )
        criterion = tdq.Criterion(target='STIX_Package/Threat_Actors/Threat_Actor/Identity/Specification/PartyName/OrganisationName/SubDivisionName', test=test)
        criteria = tdq.Criteria(OP_AND, criterion=[criterion])
        q = tdq.DefaultQuery(CB_STIX_XML_111, criteria)
        pp = tm11.PollParameters()
        pr = tm11.PollRequest(
                message_id=generate_message_id(),
                collection_name='default',
                poll_parameters=pp)
        #msg = self.send_poll_request('/services/test_poll_1/', VID_TAXII_XML_11, pr)
        msg = make_request('/services/test_poll_1/', 
                              pr.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_POLL_RESPONSE)
        if len(msg.content_blocks) != 1:
            raise ValueError('Got %s CBs' % len(msg.content_blocks))

class PollRequestTests10(TestCase):
    fixtures = ['test_data.json']
    pass

class PollFulfillmentTests11(TestCase):
    fixtures = ['test_data.json']
    pass

class CollectionInformationTests11(TestCase):
    
    fixtures = ['test_data.json']
    
    def test_01(self):
        """
        Send a collection information request, look to get a collection information response back
        """
        cir = tm11.CollectionInformationRequest(generate_message_id())
        msg = make_request(COLLECTION_MGMT_11_PATH, 
                              cir.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_COLLECTION_INFORMATION_RESPONSE)
        
        # client = tc.HttpClient()
        # client.setProxy(tc.HttpClient.NO_PROXY)
        # cir = tm11.CollectionInformationRequest(generate_message_id())
        # resp = client.callTaxiiService2(HOST, COLLECTION_MGMT_11_PATH, VID_TAXII_XML_11, cir.to_xml(), PORT)
        # msg = t.get_message_from_http_response(resp, cir.message_id)
        # if msg.message_type != MSG_COLLECTION_INFORMATION_RESPONSE:
            # raise ValueError('Expected Collection Information Response. Got: %s.\r\n%s' % \
                             # (msg.message_type, msg.to_xml(pretty_print=True)) )

class FeedInformationTests10(TestCase):
    
    fixtures = ['test_data.json']
    
    def test_01(self):
        """
        Send a feed information request, look to get a feed information response back
        """
        
        fir = tm10.FeedInformationRequest(generate_message_id())
        msg = make_request(COLLECTION_MGMT_11_PATH, 
                              fir.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_10, False), 
                              MSG_FEED_INFORMATION_RESPONSE)
        
        # client = tc.HttpClient()
        # client.setProxy(tc.HttpClient.NO_PROXY)
        # fir = tm10.FeedInformationRequest(generate_message_id())
        # resp = client.callTaxiiService2(HOST, COLLECTION_MGMT_11_PATH, VID_TAXII_XML_10, fir.to_xml(), PORT)
        # msg = t.get_message_from_http_response(resp, fir.message_id)
        # if msg.message_type != MSG_FEED_INFORMATION_RESPONSE:
            # raise ValueError('Expected Feed Information Response. Got: %s.\r\n%s' % \
                             # (msg.message_type, msg.to_xml(pretty_print=True)) )

class SubscriptionTests11(TestCase):
    
    fixtures = ['test_data.json']
    
    # Make sure to test query in here
    pass

class SubscriptionTests10(TestCase):
    
    fixtures = ['test_data.json']
    
    pass

class DiscoveryTests11(TestCase):
    
    fixtures = ['test_data.json']
    
    def test_01(self):
        """
        Send a discovery request, look to get a discovery response back
        """
        
        dr = tm11.DiscoveryRequest(generate_message_id())
        msg = make_request(DISCOVERY_11_PATH, 
                              dr.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_11, False), 
                              MSG_DISCOVERY_RESPONSE)
        
        # client = tc.HttpClient()
        # client.setProxy(tc.HttpClient.NO_PROXY)
        # dr = tm11.DiscoveryRequest(generate_message_id())
        # resp = client.callTaxiiService2(HOST, DISCOVERY_11_PATH, VID_TAXII_XML_11, dr.to_xml(), PORT)
        # msg = t.get_message_from_http_response(resp, dr.message_id)
        # if msg.message_type != MSG_DISCOVERY_RESPONSE:
            # raise ValueError('Expected Discovery Response. Got: %s.\r\n%s' % \
                             # (msg.message_type, msg.to_xml(pretty_print=True)) )

class DiscoveryTests10(TestCase):
    
    fixtures = ['test_data.json']
    
    def test_01(self):
        """
        Send a discovery request, look to get a discovery response back
        """
        
        dr = tm10.DiscoveryRequest(generate_message_id())
        msg = make_request(DISCOVERY_11_PATH, 
                              dr.to_xml(), 
                              get_headers(VID_TAXII_SERVICES_10, False), 
                              MSG_DISCOVERY_RESPONSE)
        
        # client = tc.HttpClient()
        # client.setProxy(tc.HttpClient.NO_PROXY)
        # dr = tm10.DiscoveryRequest(generate_message_id())
        # resp = client.callTaxiiService2(HOST, DISCOVERY_10_PATH, VID_TAXII_XML_10, dr.to_xml(), PORT)
        # msg = t.get_message_from_http_response(resp, dr.message_id)
        # if msg.message_type != MSG_DISCOVERY_RESPONSE:
            # raise ValueError('Expected Discovery Response. Got: %s.\r\n%s' % \
                             # (msg.message_type, msg.to_xml(pretty_print=True)) )


if __name__ == "__main__":
    unittest.main()
