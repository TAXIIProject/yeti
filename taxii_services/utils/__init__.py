# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

def get_source_ip(request):
    """Given a request object, returns the source IP used to make the request."""
    if request is None: 
        return None
    
    x_header = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_header.split(',')[0] if x_header else request.META.get('REMOTE_ADDR')
    
    return ip
