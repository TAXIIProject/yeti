# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file

__version__ = "2.0a5"

import django
import taxii_services

django.setup()
taxii_services.register_admins()
taxii_services.register_message_handlers()
