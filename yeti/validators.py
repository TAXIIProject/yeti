######################################################################################
#                                                                                    #
# Copyright (C) 2012-2013 - The MITRE Corporation. All Rights Reserved.              #
#                                                                                    #
# By using the software, you signify your aceptance of the terms and                 #
# conditions of use. If you do not agree to these terms, do not use the software.    #
#                                                                                    #
# For more information, please refer to the license.txt file.                        #
#                                                                                    #
######################################################################################

from django.core.exceptions import ValidationError

import OpenSSL



#Validate that the certificate is a valid certificate
def CertificateValidator(string_value):
	try:
		x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, string_value)
		x509.get_subject().get_components()
		pass
	except Exception as e:
		raise ValidationError(u'Certificate not a valid PEM x509 certificate: %s' % e)
