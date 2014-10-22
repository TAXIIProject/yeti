YETI
--------

YETI is a proof-of-concept implementation of the [Trusted Automated eXchange of Indicator Information](http://taxii.mitre.org)
(TAXII), created to help developers implement and test their own TAXII applications and help non-developers learn more about
TAXII.

## Overview
YETI is a proof-of-concept implementation of TAXII that supports the Inbox, Poll and Discovery services defined by the 
[TAXII Services Specification](http://taxii.mitre.org/specifications/version1.1/TAXII_Services_Specification.pdf). 
YETI was written in Python 2.7 and utilizes the  Django 1.5 web application framework. Releases of YETI will be 
[tagged](http://learn.github.com/p/tagging.html) and can be found [HERE](https://github.com/TAXIIProject/yeti/tags).

Once [deployed](https://github.com/TAXIIProject/yeti/wiki/Deployment), users can interact with YETI via the inbox,
discovery, and poll client scripts bundled with YETI and found within the scripts directory.

## Dependencies
* [Django](https://www.djangoproject.com/)
* [libtaxii](https://pypi.python.org/pypi/libtaxii/)
* [taxii_services] (https://pypi.python.org/pypi/taxii-services)
 * Specific versions of YETI 2.0a depend on specific version of taxii_services:
 * YETI 2.0a3 depends on taxii_services 0.2
 * YETI 2.0a2 depends on taxii_services 0.1.2
* [python-dateutil](https://pypi.python.org/pypi/python-dateutil)
* [pyOpenSSL](https://pypi.python.org/pypi/pyOpenSSL)

## Versioning
Releases of YETI will be given 'major.minor.revision' version numbers, where 'major' and
'minor' correspond to the TAXII version being supported. The 'revision' number is used to 
indicate new versions of YETI.

## Getting Started
To start using YETI, please refer to the bundled [INSTALL](https://github.com/TAXIIProject/yeti/blob/master/INSTALL)
file or the [Deployment](https://github.com/TAXIIProject/yeti/wiki/Deployment) section of the YETI wiki.

## Feedback 
You are encouraged to provide feedback by commenting on open issues or signing up for the TAXII
discussion list and posting your questions (http://taxii.mitre.org/community/registration.html).

## License
For license information, see the LICENSE.txt file.
