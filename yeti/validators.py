# Copyright (C) 2013 - The MITRE Corporation
# For license information, see the LICENSE.txt file


from django.core.exceptions import ValidationError

#Validate that the certificate is a valid certificate
def CertificateValidator(string_value):
    try:
        import OpenSSL
        x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, string_value)
        x509.get_subject().get_components()
        pass
    except Exception as e:
        raise ValidationError(u'Certificate not a valid PEM x509 certificate: %s' % e)
