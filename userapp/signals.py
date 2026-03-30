from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from django.conf import settings

User = settings.AUTH_USER_MODEL

# REMOVED create_user_profile form.save() handles this explicitly
# REMOVED save_user_profile unnecessary and risky on shell user creation
# REMOVED assign_member_group form.save() handles this explicitly