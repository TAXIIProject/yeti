#!/usr/bin/env python
# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import sys

from optparse import OptionParser

import libtaxii as t
import libtaxii.messages as tm
import libtaxii.clients as tc
import StringIO

#http://stix.mitre.org/language/version1.0/#samples
#http://stix.mitre.org/language/version1.0/stix_v1.0_samples_20130408.zip
stix_watchlist = '''<!--
	STIX IP Watchlist Example
	
	Copyright (c) 2013, The MITRE Corporation. All rights reserved. 
    The contents of this file are subject to the terms of the STIX License located at http://stix.mitre.org/about/termsofuse.html.
    
	This example demonstrates a simple usage of STIX to represent a list of IP address indicators (watchlist of IP addresses). Cyber operations and malware analysis centers often share a list of suspected malicious IP addresses with information about what those IPs might indicate. This STIX package represents a list of three IP addresses with a short dummy description of what they represent.
	
	It demonstrates the use of:
	
	   * STIX Indicators
	   * CybOX within STIX
	   * The CybOX Address Object (IP)
	   * CybOX Patterns (apply_condition="ANY")
	   * Controlled vocabularies
	
	Created by Mark Davidson
-->
<stix:STIX_Package
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:stix="http://stix.mitre.org/stix-1"
    xmlns:indicator="http://stix.mitre.org/Indicator-2"
    xmlns:cybox="http://cybox.mitre.org/cybox-2"
    xmlns:AddressObject="http://cybox.mitre.org/objects#AddressObject-2"
    xmlns:cyboxVocabs="http://cybox.mitre.org/default_vocabularies-2"
    xmlns:stixVocabs="http://stix.mitre.org/default_vocabularies-1"
    xmlns:example="http://example.com/"
    xsi:schemaLocation="
    http://stix.mitre.org/stix-1 http://stix.mitre.org/XMLSchema/core/1.0/stix_core.xsd
    http://stix.mitre.org/Indicator-2 http://stix.mitre.org/XMLSchema/indicator/2.0/indicator.xsd
    http://cybox.mitre.org/default_vocabularies-2 http://cybox.mitre.org/XMLSchema/default_vocabularies/2.0.0/cybox_default_vocabularies.xsd
    http://stix.mitre.org/default_vocabularies-1 http://stix.mitre.org/XMLSchema/default_vocabularies/1.0.0/stix_default_vocabularies.xsd
    http://cybox.mitre.org/objects#AddressObject-2 http://cybox.mitre.org/XMLSchema/objects/Address/2.0/Address_Object.xsd"
    id="example:STIXPackage-33fe3b22-0201-47cf-85d0-97c02164528d"
    >
    <stix:STIX_Header>
        <stix:Title>Example watchlist that contains IP information.</stix:Title>
        <stix:Package_Intent xsi:type="stixVocabs:PackageIntentVocab-1.0">Indicators - Watchlist</stix:Package_Intent>
    </stix:STIX_Header>
    <stix:Indicators>
        <stix:Indicator xsi:type="indicator:IndicatorType" id="example:Indicator-33fe3b22-0201-47cf-85d0-97c02164528d">
            <indicator:Type xsi:type="stixVocabs:IndicatorTypeVocab-1.0">IP Watchlist</indicator:Type>
            <indicator:Description>Sample IP Address Indicator for this watchlist. This contains one indicator with a set of three IP addresses in the watchlist.</indicator:Description>
            <indicator:Observable  id="example:Observable-1c798262-a4cd-434d-a958-884d6980c459">
                <cybox:Object id="example:Object-1980ce43-8e03-490b-863a-ea404d12242e">
                    <cybox:Properties xsi:type="AddressObject:AddressObjectType" category="ipv4-addr">
                        <AddressObject:Address_Value condition="Equals" apply_condition="ANY">10.0.0.0,10.0.0.1,10.0.0.2</AddressObject:Address_Value>
                    </cybox:Properties>
                </cybox:Object>
            </indicator:Observable>
        </stix:Indicator>
    </stix:Indicators>
</stix:STIX_Package>'''

def main():
    parser = OptionParser()
    parser.add_option("--host", dest="host", default="localhost", help="Host where the Inbox Service is hosted. Defaults to localhost.")
    parser.add_option("--port", dest="port", default="8080", help="Port where the Inbox Service is hosted. Defaults to 8080.")
    parser.add_option("--path", dest="path", default="/services/inbox/default/", help="Path where the Inbox Service is hosted. Defaults to /services/inbox/default/.")
    parser.add_option("--content-binding", dest="content_binding", default=t.CB_STIX_XML_10, help="Content binding of the Content Block to send. Defaults to %s" % t.CB_STIX_XML_10 )
    parser.add_option("--content-file", dest="content_file", default=stix_watchlist, help="Content of the Content Block to send. Defaults to a STIX watchlist.")

    (options, args) = parser.parse_args()

    if options.content_file is stix_watchlist:
        c = StringIO.StringIO(stix_watchlist)
    else:
        c = open(options.content_file, 'r')
    
    cb = tm.ContentBlock(options.content_binding, c.read())

    inbox_message = tm.InboxMessage(message_id = tm.generate_message_id(), content_blocks=[cb])
    inbox_xml = inbox_message.to_xml()

    print "Inbox Message: \r\n", inbox_xml
    client = tc.HttpClient()
    client.setProxy('noproxy')
    resp = client.callTaxiiService2(options.host, options.path, t.VID_TAXII_XML_10, inbox_xml, options.port)
    response_message = t.get_message_from_http_response(resp, '0')
    print "Response Message: \r\n", response_message.to_xml()

if __name__ == "__main__":
    main()











