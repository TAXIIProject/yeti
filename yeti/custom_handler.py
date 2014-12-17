# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import taxii_services as ts
from taxii_services.message_handlers.base_handlers import BaseMessageHandler
import libtaxii.messages_11 as tm11


class MyCustomHandler(BaseMessageHandler):
    """
    Does the same thing as the Built-in Discovery Request Handler,
    plus prints a statement.
    Just an example of how to extend MessageHandler
    """

    #Indicate to taxii_services which request messages are supported by this handler
    supported_request_messages = [tm11.DiscoveryRequest]

    #Indicate to taxii_services the version of this message handler
    version = "1"
    
    @staticmethod
    def handle_message(discovery_service, discovery_request, django_request):
        # Your custom code would go in here.
        print "MyCustomHandler is being called"
        # Chain together all the enabled services that this discovery service advertises
        discovery_response = discovery_service.to_discovery_response_11(discovery_request.message_id)
        return discovery_response

#ts.register_message_handler(MyCustomHandler, name="MySuperHandler")