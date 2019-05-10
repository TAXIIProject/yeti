#!/bin/sh 

python manage.py migrate --run-syncdb
python manage.py runserver --insecure 0.0.0.0:8080
