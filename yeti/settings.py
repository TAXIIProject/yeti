# Copyright (c) 2014, The MITRE Corporation. All rights reserved.
# For license information, see the LICENSE.txt file
# Django settings for yeti project.

import os
import sys
import django


sys.path.insert(0, os.path.dirname(__file__))

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# calculated paths for django and the site
DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT   = os.path.dirname(os.path.realpath(__file__))

# Note: If DEBUG is changed to "False", the SECRET_KEY must be changed to a new, secret value
DEBUG = True
TEMPLATE_DEBUG = DEBUG
APPEND_SLASH = True
TEMP_DIR = os.path.join(SITE_ROOT, "tmp")

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DB_PATH = os.path.join(os.path.dirname(SITE_ROOT), 'sqlite3.db') # one directory up from the SITE_ROOT

# YETI is configured to use SQLLite by default. To change
# the database used by YETI, see the Django documentation on 
# databases: https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.sqlite3',
        'NAME':     DB_PATH,
        # The following settings are not used with sqlite3:
        #'USER': '',
        #'PASSWORD': '',
        #'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        #'PORT': '',                      # Set to empty string for default.
    }
}


# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'extras/media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = os.path.join(SITE_ROOT, 'extras/static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
# https://docs.djangoproject.com/en/1.7/ref/settings/#std:setting-SECRET_KEY
DEFAULT_SECRET_KEY = 'gjk*d)_-o2v5zr7!zr)^h2$1%fs&jp^q!_gnv8&x)d-*!87u0^'
SECRET_KEY = DEFAULT_SECRET_KEY

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'taxii_services.middleware.StatusMessageExceptionMiddleware'
    #'taxii_services.middleware.ProcessExceptionMiddleware',#TODO: What goes on with this?
    #'django.contrib.auth.middleware.RemoteUserMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

#AUTHENTICATION_BACKENDS = (
#    'django.contrib.auth.backends.RemoteUserBackend',
#)


FIXTURE_DIRS = (#Shouldn't be necessary, but the initial data wasn't loading otherwise
   './yeti/fixtures',
)

ROOT_URLCONF = 'yeti.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'yeti.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
    'taxii_services',
    'solo',
    'yeti',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOG_LEVEL = "DEBUG"

LOG_DIRECTORY = os.path.join(SITE_ROOT, "log")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(message)s'
        },
        'normal': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'normal': {
            'level': LOG_LEVEL,
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': os.path.join(LOG_DIRECTORY, 'yeti.log'),
        },
        'stdout': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        
    },
    'loggers': {
        'yeti': {
            'handlers': ['normal','stdout'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'taxii_services': {
            'handlers': ['normal','stdout'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
    }
}


# Test to see if secret key has been defined. If not, raise a useful error message

if SECRET_KEY == DEFAULT_SECRET_KEY and DEBUG is False:
    raise ValueError("YETI is being run in non-debug mode and the SECRET_KEY has not been changed.")
