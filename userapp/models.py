from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary.models import CloudinaryField
from datetime import date

# Create your models here.
class CustomUser(AbstractUser):
    # class Roles(models.TextChoices):
    #     PASTOR = "PASTOR", "Pastor"
    #     LEADER = "LEADER", "Leader"
    #     DG_LEADER = "DG_LEADER", "DG_Leader"
    #     MEMBER = "MEMBER", "Member"

    # role = models.CharField(
    #     max_length=20,
    #     choices=Roles.choices,
    #     default=Roles.MEMBER
    # )
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username
    
class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="profile")
    DoB = models.DateField(blank=True, null=True)
    school = models.TextField(blank=True)
    workplace = models.TextField(blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    campus = models.CharField(max_length=255, blank=True)
    profile_pic = CloudinaryField("image", null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.DoB.year - (
            (today.month, today.day) < (self.DoB.month, self.DoB.day)
        )