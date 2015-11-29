# YETI

A proof-of-concept implementation of the [Trusted Automated eXchange of Indicator Information](http://taxiiproject.github.io/) (TAXII).

## Overview

YETI is a proof-of-concept implementation of TAXII that supports the Inbox,
Poll and Discovery services defined by the [TAXII Services Specification](http://taxiiproject.github.io/releases/1.1/TAXII_Services_Specification.pdf).
YETI was written for Python 2.7 and utilizes the Django 1.7 web application
framework. It created to help developers implement and test their own TAXII
applications and help non-developers learn more about TAXII.

[View YETI Releases](https://github.com/TAXIIProject/yeti/releases)

## Getting Started

View our [Getting Started](http://yeti.readthedocs.org/en/latest/getting_started.html)
page for installation instructions. Once installed (either locally or on a
remote server), users can interact with YETI using the provided
[scripts](scripts/), or any other TAXII client.

## Dependencies

* [Django](https://www.djangoproject.com/)
* [django-solo](https://pypi.python.org/pypi/django-solo)
* [libtaxii](https://pypi.python.org/pypi/libtaxii/)
* [taxii_services] (https://pypi.python.org/pypi/taxii-services)

NOTE: Specific versions of YETI 2.0 depend on specific versions of
`taxii_services`:

* YETI 2.0a3 depends on `taxii_services` 0.2 or later
* YETI 2.0a2 depends on `taxii_services` 0.1.2

NOTE: Versions 1.x of YETI included functionality now provided by the
`taxii-services` library. Prior to version 2.0,  YETI needs only Django and
libtaxii, along with the following additional requirements:
*
* [python-dateutil](https://pypi.python.org/pypi/python-dateutil)
* [pyOpenSSL](https://pypi.python.org/pypi/pyOpenSSL)

## Versioning

As of Version 2.0, YETI uses [semantic versioning](http://semver.org).

Older versions of YETI (prior to 2.0) were given `major.minor.revision` version
numbers, where `major` and `minor` corresponded to the supported TAXII version.
The `revision` number was used to indicate new versions of YETI.

## Feedback

Feedback is welcome, either directly though GitHub (issues or pull requests),
or directly to taxii@mitre.org.

## License

YETI is released under a 3-Clause BSD license. For more information, see
[LICENSE.txt](LICENSE.txt).
