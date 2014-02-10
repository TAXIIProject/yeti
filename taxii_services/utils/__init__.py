# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

import django.utils.html

def get_source_ip(request):
    """Given a request object, returns the source IP used to make the request."""
    if request is None: 
        return None
    
    x_header = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_header.split(',')[0] if x_header else request.META.get('REMOTE_ADDR')
    
    return ip


def make_safe(str_):
    """Returns a copy of the input string that is safe for logging.
    
    The following operations are performed on the string:
    - Normalize all whitespace to a single space
    - Removes trailing and leading whitespace
    - HTML-escape the string 
    """
    if str_ is None:
        return None
    
    normalized = ' '.join(str(str_).split())
    escaped = django.utils.html.escape(normalized)
    
    return escaped
