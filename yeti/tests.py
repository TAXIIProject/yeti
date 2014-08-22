# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import libtaxii as t
import libtaxii.messages_10 as tm10
import libtaxii.messages_11 as tm11
import libtaxii.taxii_default_query as tdq
import libtaxii.clients as tc
from libtaxii.constants import *
from libtaxii.common import generate_message_id

from django.test import TestCase
import urllib2

# Global params for TestCases to use
DEBUG = True
HOST = 'localhost'
PORT = 8080
PROXY_TYPE = tc.HttpClient.PROXY_HTTP
PROXY_ADDR = "http://gatekeeper.mitre.org:80"

INBOX_11_PATH = '/services/inbox/'
DISCOVERY_11_PATH = '/services/discovery/'
POLL_11_PATH = '/services/poll/'
COLLECTION_MGMT_11_PATH = '/services/collection-management/'

INBOX_10_PATH = '/services/inbox/'
DISCOVERY_10_PATH = '/services/discovery/'
POLL_10_PATH = '/services/poll/'
FEED_MGMT_10_PATH = '/services/collection-management/'

stix_watchlist_111 = '''
<!--
	STIX Domain Watchlist Example
	
	Copyright (c) 2014, The MITRE Corporation. All rights reserved. 
    The contents of this file are subject to the terms of the STIX License located at http://stix.mitre.org/about/termsofuse.html.
    
	This example demonstrates one method of representing a domain watchlist (list of malicious domains) in STIX and CybOX. It demonstrates several STIX/CybOX concepts and best practices including:
	
	   * Indicators
	   * CybOX within STIX
	   * The CybOX Domain object
	   * Controlled vocabularies
	
	Created by Mark Davidson
-->
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

class TestFailures(TestCase):
    """
    Tests all sorts of edge cases that should result in a 
    "graceful" failure and not a stack trace response
    """
    
    def base_test(self, post_data, path, header_dict, message_type, expected_code=200):
        """
        Reusable base_test for other tests to use.
        Uses urllib2 directly instead of tc.HttpClient
        so that various "incorrect" things can be done
        for testing purposes
        """
        handler_list = []
        handler_list.append(urllib2.ProxyHandler({PROXY_TYPE: PROXY_ADDR}))
        opener = urllib2.build_opener(*handler_list)
        urllib2.install_opener(opener)
        url = "http://" + HOST + ':' + str(PORT) + path
        req = urllib2.Request(url, post_data, header_dict)
        resp = urllib2.urlopen(req)
        if resp.code != expected_code:
            msg = resp.read()
            if DEBUG:
                print msg
            raise ValueError("Response code was not %s. Was: %s" % (str(expected_code), str(resp.code)) )
        
        msg = t.get_message_from_http_response(resp, '0')
        if DEBUG:
            print msg.to_xml(pretty_print=True)
        if msg.message_type != message_type:
            raise ValueError("Incorrect message type sent in response. Expected: %s. Got: %s" % (message_type, msg.message_type) )
    
    def test_01(self):
        """
        Sends an Inbox Message to an invalid URL. 
        Should get back a 404
        """
        inbox_message = tm11.InboxMessage(generate_message_id())
        client = tc.HttpClient()
        client.setProxy(PROXY_TYPE, PROXY_ADDR)
        resp = client.callTaxiiService2(HOST, '/PathThatShouldNotWork/', VID_TAXII_XML_11, inbox_message.to_xml(), port=PORT)
        if resp.code != 404:
            msg = resp.read()
            if DEBUG:
                print msg
            raise ValueError("Response code was not 404. Was: %s" % str(resp.code))
    
    def test_02(self):
        """
        Tests sending a GET request to the server. Should result in a BAD MESSAGE
        """
        client = tc.HttpClient()
        client.setProxy(PROXY_TYPE, PROXY_ADDR)
        resp = client.callTaxiiService2(HOST, INBOX_11_PATH, VID_TAXII_XML_11, post_data=None, port=PORT)
        if resp.code != 200:
            msg = resp.read()
            if DEBUG:
                print msg
            raise ValueError("Response was not 200. Was: %s" % str(resp.code))
        msg = t.get_message_from_http_response(resp, '0')
        if DEBUG:
            print msg.to_xml(pretty_print=True)
        if msg.message_type != MSG_STATUS_MESSAGE:
            raise ValueError("Incorrect message type sent in response: %s" % msg.message_type)
    
    def test_03(self):
        """
        Send an XML fragment to the server
        """
        client = tc.HttpClient()
        client.setProxy(PROXY_TYPE, PROXY_ADDR)
        resp = client.callTaxiiService2(HOST, INBOX_11_PATH, VID_TAXII_XML_11, post_data='<XML_that_is_not_well_formed>', port=PORT)
        if resp.code != 200:
            msg = resp.read()
            if DEBUG:
                print msg
            raise ValueError("Response was not 200. Was: %s" % str(resp.code))
        msg = t.get_message_from_http_response(resp, '0')
        if DEBUG:
            print msg.to_xml(pretty_print=True)
        if msg.message_type != MSG_STATUS_MESSAGE:
            raise ValueError("Incorrect message type sent in response: %s" % msg.message_type)
    
    def test_04(self):
        """
        Send schema-invalid XML
        """
        client = tc.HttpClient()
        client.setProxy(PROXY_TYPE, PROXY_ADDR)
        resp = client.callTaxiiService2(HOST, INBOX_11_PATH, VID_TAXII_XML_11, post_data='<well_formed_schema_invalid_xml/>', port=PORT)
        if resp.code != 200:
            msg = resp.read()
            if DEBUG:
                print msg
            raise ValueError("Response was not 200. Was: %s" % str(resp.code))
        msg = t.get_message_from_http_response(resp, '0')
        if DEBUG:
            print msg.to_xml(pretty_print=True)
        if msg.message_type != MSG_STATUS_MESSAGE:
            raise ValueError("Incorrect message type sent in response: %s" % msg.message_type)
    
    # The next few tests test headers presence/absence
    # and unsupported values
    
    def test_05(self):
        """
        Send a message without the Accept header 
        """
        header_dict = {'Accept': 'application/xml',
                       'Content-Type': 'application/xml',
                       'X-TAXII-Accept': 'urn:taxii.mitre.org:messages:xml:1.1'
                       'X-TAXII-Content-Type': 'urn:taxii.mitre.org:message:xml:1.1',
                       'X-TAXII-Protocol': 'urn:taxii.mitre.org:protocol:https:1.0',
                       'X-TAXII-Services': 'urn:taxii.mitre.org:services:1.1'}
        
        handler_list = []
        handler_list.append(urllib2.ProxyHandler({PROXY_TYPE: PROXY_ADDR}))
        opener = urllib2.build_opener(*handler_list)
        urllib2.install_opener(opener)
        url = "http://" + HOST + ':' + str(PORT) + INBOX_11_PATH
        req = urllib2.Request(url, post_data, header_dict)
        response = urllib2.urlopen(req)

class InboxTests11(TestCase):
    pass

class InboxTests10(TestCase):
    pass

class PollRequestTests11(TestCase):
    # Make sure query tests are in here
    pass

class PollRequestTests10(TestCase):
    pass

class PollFulfillmentTests11(TestCase):
    pass

class CollectionInformationTests11(TestCase):
    pass

class CollectionInformationTests10(TestCase):
    pass

class SubscriptionTests11(TestCase):
    # Make sure to test query in here
    pass

class SubscriptionTests10(TestCase):
    pass

class DiscoveryTests11(TestCase):
    pass

class DiscoveryTests10(TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
