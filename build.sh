#!/usr/bin/env bash
set -e

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --run-syncdb
python manage.py generate_slots
python manage.py seed_cities
python manage.py seed_initial_data
python manage.py shell -c "
from django.contrib.auth.models import User

User.objects.filter(username='admin').exists() or User.objects.create_superuser(
    username='admin',
    email='back@fis.se',
    password='deneme122345'
)
"