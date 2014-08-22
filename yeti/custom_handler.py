# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import taxii_services.taxii_handlers as th
import taxii_services.handlers as h
import libtaxii.messages_11 as tm11

class MyCustomHandler(th.MessageHandler):
    """
    Does the same thing as the Built-in Discovery Request Handler,
    plus prints a statement.
    Just an example of how to extend MessageHandler
    """
    supported_request_messages = [tm11.DiscoveryRequest]
    
    @staticmethod
    def handle_message(discovery_service, discovery_request, django_request):        
        print "MyCustomHandler is being called"
        # Chain together all the enabled services that this discovery service advertises
        advertised_services = list(chain(discovery_service.advertised_discovery_services.filter(enabled=True),
                                         discovery_service.advertised_poll_services.filter(enabled=True),
                                         discovery_service.advertised_inbox_services.filter(enabled=True),
                                         discovery_service.advertised_collection_management_services.filter(enabled=True)))
        
        # Create the stub DiscoveryResponse
        discovery_response = tm11.DiscoveryResponse(tm11.generate_message_id(), discovery_request.message_id)
        
        # Iterate over advertised services, creating a service instance for each
        for service in advertised_services:
            service_instances = taxiifiers.service_to_service_instances(service)
            discovery_response.service_instances.extend(service_instances)
        
        # Return the Discovery Response
        return discovery_response

#h.register_message_handler(MyCustomHandler, name="MySuperHandler")