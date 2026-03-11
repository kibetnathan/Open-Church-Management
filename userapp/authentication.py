import firebase_admin
from firebase_admin import auth
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions

User = get_user_model()

class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            print("DEBUG: No Bearer token found")  # ← Add this line
            return None

        parts = auth_header.split(' ')
        if len(parts) != 2:
            return None

        id_token = parts[1]
        try:
            decoded_token = auth.verify_id_token(id_token)
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Firebase Error: {str(e)}')

        uid = decoded_token.get('uid')
        email = decoded_token.get('email')

        if not uid:
            raise exceptions.AuthenticationFailed('UID not found in token')

        try:
            user = User.objects.filter(firebase_uid=uid).first()
            if not user:
                user = User.objects.filter(email=email).first()
                if user:
                    user.firebase_uid = uid
                    user.save()
                else:
                    user, _ = User.objects.get_or_create(
                        username=uid,
                        defaults={
                            'email': email,
                            'firebase_uid': uid,
                            'is_active': True,
                        }
                    )
                    if not user.firebase_uid:
                        user.firebase_uid = uid
                        user.save()
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Database Sync Error: {str(e)}')

        return (user, None)  # ← this was missing entirely