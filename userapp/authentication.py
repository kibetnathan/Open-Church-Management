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

        try:
            user = User.objects.filter(firebase_uid=uid).first()
            if not user:
                # Check if the email exists to link an old account
                user = User.objects.filter(email=email).first()
                
                if user:
                    user.firebase_uid = uid
                    user.save()
                else:
                    # FIX: Use the UID as the temporary username.
                    # This avoids the "Email already exists" constraint error.
                    user = User.objects.create(
                        username=uid, # Use UID here, NOT email
                        email=email, 
                        firebase_uid=uid,
                        is_active=True
                    )
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Database Sync Error: {str(e)}')