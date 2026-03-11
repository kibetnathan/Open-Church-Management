from django.utils import timezone
from django.db import models
from django.conf import settings
from userapp.models import Profile
from cloudinary.models import CloudinaryField
class LeadershipTeam(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="leadership_teams"
    )

    def __str__(self):
        return self.name
    
class Department(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="serving_team_leader",
        on_delete=models.SET_NULL,
        null=True,
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="serving_team",
        blank=True
    )

class Services(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="services"
    )
    crew = models.ManyToManyField(
        Department,
        related_name="services_crew",
        blank=True
    )
    pastor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="services_pastor"
    )

    def __str__(self):
        return self.name

    @property
    def equipment(self):
        return getattr(self, "assigned_equipment", None)
    
class Equipment(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.PositiveIntegerField(default=1)
    image = CloudinaryField('image', blank=True, null=True)
    assigned_service = models.OneToOneField(
        Services,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_equipment"
    )
    assigned_department = models.OneToOneField(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_equipment"
    )
# Services
class FellowshipGroup(models.Model):
    # in dgs leaders are also members
    name = models.CharField(max_length=255)
    description = models.TextField()
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="discipleship_group_leader"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="discipleship_group",
        blank=True
    )
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.leader not in self.members.all():
            self.members.add(self.leader)

    def __str__(self):
        return (f'{self.name} led by {self.leader}')
    
    def get_leader(self):
        return self.leader

class Course(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    start_date = models.DateField(default=timezone.now)
    expected_duration= models.DurationField(help_text="Expected duration of the course in weeks")
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="ropes_class_leader",
        on_delete=models.SET_NULL,
        null=True,
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="ropes_class",
        blank=True
    )


# class MinistryData(models.Model):
#     user = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         related_name="ministry_data",
#         on_delete=models.CASCADE,
#     )
#     @property
#     def name(self):
#         return f"{self.user.first_name} {self.user.last_name}"
#     @property
#     def campus(self):
#         if hasattr(self.user, "profile") and self.user.profile:
#             return self.user.profile.campus
#         return None
#     dg = models.ForeignKey(
#         DiscipleshipGroup,
#         on_delete=models.SET_NULL,
#         null=True,
#         related_name="dg"
#     )
#     department = models.ManyToManyField(
#         ServingTeam,
#         blank=True,
#         related_name="department"
#     )