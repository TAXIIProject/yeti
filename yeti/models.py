# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models.signals import post_save, post_delete
import datetime
from dateutil.tz import tzutc
import validators
import settings

class Certificate(models.Model):
	"""Manages SSL/TLS Certificates for YETI/Apache authentication"""
	title = models.CharField(max_length=64)
	description = models.TextField(blank=True)
	subject = models.CharField(max_length=255, unique=True, editable=False, default='Unassigned')
	issuer = models.CharField(max_length=255, editable=False, default='Unassigned')
	pem_certificate = models.TextField(validators=[validators.CertificateValidator])
	
	date_created = models.DateTimeField(default=lambda:datetime.datetime.now(tzutc()))
	date_updated = models.DateTimeField(auto_now=True)
	
	def __unicode__(self):
		return self.title
	
	def clean(self):
		try:
			import OpenSSL
			x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, self.pem_certificate)
			x509subject = x509.get_subject()
			self.subject = str(x509subject)[18:-2]
			x509issuer = x509.get_issuer()
			self.issuer = str(x509issuer)[18:-2]
		except ImportError:
			raise ValidationError(message="Cannot validate certificate: pyOpenSSL is not installed.")
		except Exception as ex:
			raise ValidationError(message="Could not validate certificate [%s]" % (str(ex)))

def do_export_certs(sender, **kwargs):
	"""
	Overwrites the client certificate file with all the stored
	Certificate objects. To modify the location of the client
	certificate file, edit the settings.CERT_EXPORT_LOCATION 
	configuration option.
	"""
	export_location = settings.CERT_EXPORT_LOCATION
	export_file = open(export_location, 'w')
	all_certs = Certificate.objects.all()
	
	for cert in all_certs:
		export_file.write(cert.pem_certificate + '\r\n')
	
	export_file.flush()
	export_file.close()

post_save.connect(do_export_certs, sender=Certificate)
post_delete.connect(do_export_certs, sender=Certificate)

