# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

import logging
from datetime import datetime

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, Http404, HttpResponseNotAllowed, HttpResponseRedirect, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

import taxii_services.utils.handlers as handlers
from taxii_services.models import DataFeed, ContentBlock
import libtaxii.messages as tm



@csrf_exempt
def inbox_service(request, dest_feed_name=None):
    logger = logging.getLogger('yeti.taxii_services.views.inbox_service')
    logger.info('entering inbox service')
    
    resp = handlers.validate_taxii_request(request)
    if resp: return resp

    

    message = tm.get_message_from_xml(request.body)

@csrf_exempt
def poll_service(request, feed_name):
    logger = logging.getLogger("yeti.taxii_services.views.poll_service")
    logger.info('entering poll service')
    
    resp = handlers.validate_taxii_request(request)
    if resp: return resp
    
    message = tm.get_message_from_xml(request.body)
