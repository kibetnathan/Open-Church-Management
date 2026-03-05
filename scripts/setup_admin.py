import os
from django.contrib.auth.models import User as DjangoUser

# Create backend-only superuser (for Django admin access)
backend_username = 'backend_admin'
backend_email = os.getenv('BACKEND_ADMIN_EMAIL', 'backend@example.com')
backend_password = os.getenv('BACKEND_ADMIN_PASSWORD')

if backend_password and not DjangoUser.objects.filter(username=backend_username).exists():
    DjangoUser.objects.create_superuser(backend_username, backend_email, backend_password)
    print(f'✓ Backend superuser created: {backend_username}')
else:
    print('✓ Backend superuser already exists')