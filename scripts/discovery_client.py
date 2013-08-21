#!/usr/bin/env python
# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import argparse

import libtaxii as t
import libtaxii.messages as tm
import libtaxii.clients as tc

def main():
    parser = argparse.ArgumentParser(description="Discovery Client")
    parser.add_argument("--host", dest="host", default="localhost", help="Host where the Discovery Service is hosted. Defaults to localhost.")
    parser.add_argument("--port", dest="port", default="8080", help="Port where the Discovery Service is hosted. Defaults to 8080.")
    parser.add_argument("--path", dest="path", default="/services/discovery/", help="Path where the Discovery Service is hosted. Defaults to /services/discovery/.")
    
    args = parser.parse_args()

    discovery_req = tm.DiscoveryRequest(message_id=tm.generate_message_id())
    discovery_req_xml = discovery_req.to_xml()

    print "Discovery Request: \r\n", discovery_req_xml
    client = tc.HttpClient()
    client.setProxy('noproxy')
    resp = client.callTaxiiService2(args.host, args.path, t.VID_TAXII_XML_10, discovery_req_xml, args.port)
    response_message = t.get_message_from_http_response(resp, '0')
    print "Response Message: \r\n", response_message.to_xml()

if __name__ == "__main__":
    main()
    
