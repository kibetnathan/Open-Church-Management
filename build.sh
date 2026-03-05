#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

python manage.py shell <<END
from django.contrib.auth.models import User
import os

username = 'backend_admin'
email = os.getenv('BACKEND_ADMIN_EMAIL')
password = os.getenv('BACKEND_ADMIN_PASSWORD')

if email and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print('✓ Superuser created')
    else:
        print('✓ Superuser already exists')
else:
    print('⚠ BACKEND_ADMIN_EMAIL or BACKEND_ADMIN_PASSWORD not set')
END