# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import yeti
import taxii_services.utils.handlers as handlers
import libtaxii.messages as tm

def yeti_auth_check(func):
    def inner(request, *args, **kwargs):
        if not yeti.settings.AUTH_REQUIRED:
            return func(request, *args, **kwargs)
        elif request.user.is_authenticated():
            return func(request, *args, **kwargs)
        
        m = tm.StatusMessage(tm.generate_message_id(), '0', status_type=tm.ST_UNAUTHORIZED, message='You are not authorized to access this URL.')
        return handlers.create_taxii_response(m)
    return inner