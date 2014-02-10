# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file


from django.core.exceptions import ValidationError

#Validate that the certificate is a valid certificate
def CertificateValidator(string_value):
    try:
        import OpenSSL
        OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, string_value)
    except ImportError:
        raise ValidationError(u'Cannot validate certificate: pyOpenSSL is not installed')
    except Exception as e:
        raise ValidationError(u'Certificate not a valid PEM x509 certificate: %s' % e)
