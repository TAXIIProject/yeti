# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import sys

from optparse import OptionParser

import libtaxii as t
import libtaxii.messages as tm
import libtaxii.clients as tc

parser = OptionParser()
parser.add_option("--host", dest="host", default="localhost", help="Host where the Poll Service is hosted. Defaults to localhost.")
parser.add_option("--port", dest="port", default="8080", help="Port where the Poll Service is hosted. Defaults to 8080.")
parser.add_option("--path", dest="path", default="/services/poll/", help="Path where the Poll Service is hosted. Defaults to /poll/.")
parser.add_option("--feed", dest="feed", default="default", help="Data Feed to poll. Defaults to 'default'.")
parser.add_option("--begin_timestamp", dest="begin_ts", default=None, help="The begin timestamp for the poll request. Defaults to None.")
parser.add_option("--end_timestamp", dest="end_ts", default=None, help="The end timestamp for the poll request. Defaults to None.")

(options, args) = parser.parse_args()

poll_req = tm.PollRequest(message_id = tm.generate_message_id(),
                          feed_name = options.feed,
                          exclusive_begin_timestamp_label = options.begin_ts,
                          inclusive_end_timestamp_label = options.end_ts)
poll_req_xml = poll_req.to_xml()

print "Poll Request: \r\n", poll_req_xml
client = tc.HttpClient()
client.setProxy('noproxy')
resp = client.callTaxiiService2(options.host, options.path, t.VID_TAXII_XML_10, poll_req_xml, options.port)
response_message = t.get_message_from_http_response(resp, '0')
print "Response Message: \r\n", response_message.to_xml()












