from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from userapp.models import CustomUser
from mainapp.models import MemorizeVerse, MemorizationAttempt

FIXED_NOW = datetime(2026, 3, 25, 12, 0, 0, tzinfo=dt_timezone.utc)
STATS_URL = '/api/memorize/stats/'


def make_user(username):
    return CustomUser.objects.create_user(
        username=username, email=f'{username}@test.com', password='pw'
    )


def make_verse(user):
    return MemorizeVerse.objects.create(
        user=user,
        book_id='GEN', book_name='Genesis',
        chapter=1, verse_number=1, translation='BSB',
        verse_text='In the beginning.',
    )


def make_attempt(verse, days_ago=0):
    """Create an attempt timestamped `days_ago` days before FIXED_NOW."""
    a = MemorizationAttempt.objects.create(verse=verse, score=2, level=1)
    dt = FIXED_NOW - timedelta(days=days_ago)
    MemorizationAttempt.objects.filter(pk=a.pk).update(attempted_at=dt)
    return a


class StreakTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_three_consecutive_days(self, _):
        user = make_user('u1')
        self.client.force_authenticate(user)
        verse = make_verse(user)
        for i in range(3):
            make_attempt(verse, days_ago=i)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['streak'], 3)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_today_only(self, _):
        user = make_user('u2')
        self.client.force_authenticate(user)
        make_attempt(make_verse(user), days_ago=0)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.data['streak'], 1)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_no_attempts(self, _):
        user = make_user('u3')
        self.client.force_authenticate(user)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.data['streak'], 0)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_thirty_consecutive_days(self, _):
        user = make_user('u4')
        self.client.force_authenticate(user)
        verse = make_verse(user)
        for i in range(30):
            make_attempt(verse, days_ago=i)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.data['streak'], 30)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_gap_yesterday_breaks_streak_at_one(self, _):
        # today + 3,4,5 days ago — gap at yesterday stops the loop
        user = make_user('u5')
        self.client.force_authenticate(user)
        verse = make_verse(user)
        make_attempt(verse, days_ago=0)
        for i in (3, 4, 5):
            make_attempt(verse, days_ago=i)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.data['streak'], 1)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_no_attempt_today_streak_is_zero(self, _):
        # yesterday + day before, NOT today → loop breaks immediately
        user = make_user('u6')
        self.client.force_authenticate(user)
        verse = make_verse(user)
        make_attempt(verse, days_ago=1)
        make_attempt(verse, days_ago=2)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.data['streak'], 0)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_attempts_older_than_30_days(self, _):
        user = make_user('u7')
        self.client.force_authenticate(user)
        verse = make_verse(user)
        make_attempt(verse, days_ago=31)
        make_attempt(verse, days_ago=35)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.data['streak'], 0)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_multiple_attempts_same_day_count_as_one(self, _):
        user = make_user('u8')
        self.client.force_authenticate(user)
        verse = make_verse(user)
        for _ in range(5):
            make_attempt(verse, days_ago=0)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.data['streak'], 1)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_user_isolation(self, _):
        user_a = make_user('ua')
        user_b = make_user('ub')
        verse_a = make_verse(user_a)
        for i in range(10):
            make_attempt(verse_a, days_ago=i)
        self.client.force_authenticate(user_b)
        resp = self.client.get(STATS_URL)
        self.assertEqual(resp.data['streak'], 0)
