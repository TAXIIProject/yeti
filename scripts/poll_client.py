#!/usr/bin/env python
# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import sys

import argparse
import dateutil.parser

import libtaxii as t
import libtaxii.messages as tm
import libtaxii.clients as tc


def main():
    parser = argparse.ArgumentParser(description="Poll Client")
    parser.add_argument("--host", dest="host", default="localhost", help="Host where the Poll Service is hosted. Defaults to localhost.")
    parser.add_argument("--port", dest="port", default="8080", help="Port where the Poll Service is hosted. Defaults to 8080.")
    parser.add_argument("--path", dest="path", default="/services/poll/", help="Path where the Poll Service is hosted. Defaults to /services/poll/.")
    parser.add_argument("--feed", dest="feed", default="default", help="Data Feed to poll. Defaults to 'default'.")
    parser.add_argument("--begin_timestamp", dest="begin_ts", default=None, help="The begin timestamp (format: YYYY-MM-DDTHH:MM:SS.ssssss+/-hh:mm) for the poll request. Defaults to None.")
    parser.add_argument("--end_timestamp", dest="end_ts", default=None, help="The end timestamp (format: YYYY-MM-DDTHH:MM:SS.ssssss+/-hh:mm) for the poll request. Defaults to None.")

    args = parser.parse_args()

    try:
        if args.begin_ts:
            begin_ts = dateutil.parser.parse(args.begin_ts)
            if not begin_ts.tzinfo:
                raise ValueError
        else:
            begin_ts = None

        if args.end_ts:
            end_ts = dateutil.parser.parse(args.end_ts)
            if not end_ts.tzinfo:
                raise ValueError
        else:
            end_ts = None
    except ValueError:
        print "Unable to parse timestamp value. Timestamp should include both date and time information along with a timezone or UTC offset (e.g., YYYY-MM-DDTHH:MM:SS.ssssss+/-hh:mm). Aborting poll."
        sys.exit()

    poll_req = tm.PollRequest(message_id=tm.generate_message_id(),
                              feed_name=args.feed,
                              exclusive_begin_timestamp_label=begin_ts,
                              inclusive_end_timestamp_label=end_ts)

    poll_req_xml = poll_req.to_xml()
    print "Poll Request: \r\n", poll_req_xml
    client = tc.HttpClient()
    client.setProxy('noproxy')
    resp = client.callTaxiiService2(args.host, args.path, t.VID_TAXII_XML_10, poll_req_xml, args.port)
    response_message = t.get_message_from_http_response(resp, '0')
    print "Response Message: \r\n", response_message.to_xml()

if __name__ == "__main__":
    main()
