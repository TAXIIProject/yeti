# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

from django.http import HttpResponse, HttpResponseNotFound


def index(request):
	return HttpResponseNotFound("404 - NOT FOUND")

