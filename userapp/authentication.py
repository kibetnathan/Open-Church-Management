import firebase_admin
from firebase_admin import auth
from django.contrib.auth import get_user_model # Use this for Custom User Models
from rest_framework import authentication, exceptions

# Get your userapp.CustomUser model dynamically
User = get_user_model()

class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        # Extract the token
        parts = auth_header.split(' ')
        if len(parts) != 2:
            return None
            
        id_token = parts[1]

        try:
            # 1. Verify the token with Google/Firebase
            # check_revoked=True is safer but adds a network request
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            # Catching expired or malformed tokens
            raise exceptions.AuthenticationFailed(f'Firebase Error: {str(e)}')

        uid = decoded_token.get('uid')
        email = decoded_token.get('email')

        if not uid:
            raise exceptions.AuthenticationFailed('UID not found in token')

        # 2. Link Firebase UID to your CustomUser
        # We use the UID as the username because it's permanent and unique.
        try:
            user, created = User.objects.get_or_create(
                username=uid, 
                defaults={'email': email}
            )
            
            # If the user was just created, you might want to mark them as active
            if created:
                user.is_active = True
                user.save()
                
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Database Sync Error: {str(e)}')

        return (user, None)