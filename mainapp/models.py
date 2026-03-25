import re
from statistics import mode
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


class MemorizeVerse(models.Model):
    """A verse the user has saved to their memorization queue."""
 
    TRANSLATION_CHOICES = [
        ('BSB', 'Berean Standard Bible'),
        ('KJV', 'King James Version'),
        ('NIV', 'New International Version'),
        ('ESV', 'English Standard Version'),
        ('NASB', 'New American Standard Bible'),
    ]
 
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memorize_verses',
    )
 
    # Reference
    book_id = models.CharField(max_length=10)           # e.g. "GEN", "JHN"
    book_name = models.CharField(max_length=50)         # e.g. "Genesis", "John"
    chapter = models.PositiveSmallIntegerField()
    verse_number = models.PositiveSmallIntegerField()
    translation = models.CharField(
        max_length=10,
        choices=TRANSLATION_CHOICES,
        default='BSB',
    )
 
    # Cached text from bible.helloao.org at save time
    verse_text = models.TextField()
 
    # Spaced repetition state
    next_review = models.DateTimeField(default=timezone.now)
    interval_days = models.PositiveSmallIntegerField(default=1)
    rep_count = models.PositiveIntegerField(default=0)
    last_score = models.PositiveSmallIntegerField(default=0)     # 0–3 matching MemorizationAttempt.score
 
    added_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        unique_together = ('user', 'book_id', 'chapter', 'verse_number', 'translation')
        ordering = ['next_review']
 
    def __str__(self):
        return f'{self.user} — {self.book_name} {self.chapter}:{self.verse_number} ({self.translation})'
 
    @property
    def reference(self):
        return f'{self.book_name} {self.chapter}:{self.verse_number}'
 
    @property
    def is_due(self):
        return timezone.now() >= self.next_review
 
    # Interval ladder: 1 → 3 → 7 → 14 days
    INTERVAL_LADDER = [1, 3, 7, 14]
 
    def advance(self, score):
        """
        Update spaced repetition state after a review attempt.
 
        score:
            0 — no recall (reset to start of ladder)
            1 — partial recall (stay on current rung)
            2 — recalled with effort (advance one rung)
            3 — perfect recall (advance one rung, double the interval)
        """
        self.last_score = score
        self.rep_count += 1
 
        if score == 0:
            self.interval_days = self.INTERVAL_LADDER[0]
        elif score == 1:
            # Stay on the current rung
            pass
        else:
            # Advance one rung; if already at the top, double
            try:
                current_rung = self.INTERVAL_LADDER.index(self.interval_days)
            except ValueError:
                # interval_days may have been doubled past the ladder
                current_rung = len(self.INTERVAL_LADDER) - 1
 
            if current_rung < len(self.INTERVAL_LADDER) - 1:
                self.interval_days = self.INTERVAL_LADDER[current_rung + 1]
            else:
                self.interval_days = self.interval_days * 2
 
            if score == 3:
                self.interval_days = self.interval_days * 2
 
        self.next_review = timezone.now() + timezone.timedelta(days=self.interval_days)
        self.save()
 
 
class MemorizationAttempt(models.Model):
    """
    A single review session for one verse.
    Kept for progress history and future analytics.
    """
 
    SCORE_CHOICES = [
        (0, 'No recall'),
        (1, 'Partial recall'),
        (2, 'Recalled with effort'),
        (3, 'Perfect recall'),
    ]
 
    LEVEL_CHOICES = [
        (1, 'Level 1 — every 4th word blanked'),
        (2, 'Level 2 — every other word blanked'),
        (3, 'Level 3 — first-letter hints'),
        (4, 'Level 4 — full recall'),
    ]
 
    verse = models.ForeignKey(
        MemorizeVerse,
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    attempted_at = models.DateTimeField(auto_now_add=True)
    level = models.PositiveSmallIntegerField(choices=LEVEL_CHOICES)
    score = models.PositiveSmallIntegerField(choices=SCORE_CHOICES)
 
    class Meta:
        ordering = ['-attempted_at']
 
    def __str__(self):
        return (
            f'{self.verse.reference} — '
            f'L{self.level} score {self.score} @ {self.attempted_at:%Y-%m-%d %H:%M}'
        )


class ReadingPlan(models.Model):
    title          = models.CharField(max_length=255)
    description    = models.TextField(blank=True)
    youversion_url = models.URLField(
        help_text="Full YouVersion URL e.g. https://www.bible.com/reading-plans/1234"
    )
    cover_image    = CloudinaryField('image', null=True, blank=True)
    created_by     = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reading_plans_created',
    )
    start_date    = models.DateField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Length of the plan in days e.g. 365"
    )
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Scoping — all empty = church-wide (visible to everyone)
    fellowship_groups = models.ManyToManyField(
        FellowshipGroup, blank=True, related_name='reading_plans',
    )
    departments = models.ManyToManyField(
        Department, blank=True, related_name='reading_plans',
    )
    courses = models.ManyToManyField(
        Course, blank=True, related_name='reading_plans',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def youversion_plan_id(self):
        """Extract the numeric plan ID from the YouVersion URL."""
        match = re.search(r'/reading-plans/(\d+)', self.youversion_url)
        return match.group(1) if match else None

    @property
    def widget_url(self):
        plan_id = self.youversion_plan_id
        return f"https://www.bible.com/widgets/reading-plans/{plan_id}" if plan_id else None

    @property
    def is_church_wide(self):
        return (
            not self.fellowship_groups.exists()
            and not self.departments.exists()
            and not self.courses.exists()
        )


class CharityOrganisation(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    banner = CloudinaryField('image', blank=True, null=True)
    payment_method = models.TextField(
        blank=True,
        help_text="Payment details that congregants can use to donate",
    )
    donation_link = models.URLField(blank=True, null=True, help_text="External donation gateway URL")
    pastor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='charity_organisations_led',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='charity_organisations',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ReadingPlanMember(models.Model):
    """Tracks which users have joined a reading plan in OCM."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reading_plan_memberships',
    )
    plan = models.ForeignKey(
        ReadingPlan,
        on_delete=models.CASCADE,
        related_name='memberships',
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'plan')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user} → {self.plan.title}"
 
