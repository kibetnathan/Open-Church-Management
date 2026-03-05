#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser with custom user model
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
import os

User = get_user_model()  # This gets your CustomUser instead of default User
username = 'backend_admin'
email = os.getenv('BACKEND_ADMIN_EMAIL', 'backend@example.com')
password = os.getenv('BACKEND_ADMIN_PASSWORD', '')

if password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print('✓ Superuser created successfully')
    else:
        print('✓ Superuser already exists')
else:
    print('⚠ BACKEND_ADMIN_PASSWORD not set - skipping superuser creation')
EOF

echo "Build completed successfully"