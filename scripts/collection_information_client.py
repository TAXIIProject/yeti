#!/usr/bin/env python
# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import sys

import argparse
import dateutil.parser

import libtaxii as t
import libtaxii.messages_11 as tm11
import libtaxii.clients as tc


def main():
    parser = argparse.ArgumentParser(description="Collection Information Client")
    parser.add_argument("--host", dest="host", default="localhost", help="Host where the Poll Service is hosted. Defaults to localhost.")
    parser.add_argument("--port", dest="port", default="8080", help="Port where the Poll Service is hosted. Defaults to 8080.")
    parser.add_argument("--path", dest="path", default="/services/collection_management/", help="Path where the Collection Management Service is hosted. Defaults to /services/collection_management/.")

    args = parser.parse_args()

    collection_information_request = tm11.CollectionInformationRequest(message_id=tm11.generate_message_id())

    collection_information_request_xml = collection_information_request.to_xml()
    print "Collection Information Request: \r\n", collection_information_request_xml
    client = tc.HttpClient()
    client.setProxy('noproxy') 
    resp = client.callTaxiiService2(args.host, args.path, t.VID_TAXII_XML_11, collection_information_request_xml, args.port)
    response_message = t.get_message_from_http_response(resp, '0')
    print "Response Message: \r\n", response_message.to_xml()

if __name__ == "__main__":
    main()
