from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from userapp.models import CustomUser
from mainapp.models import MemorizeVerse

FIXED_NOW = datetime(2026, 3, 25, 12, 0, 0, tzinfo=dt_timezone.utc)


def make_user():
    return CustomUser.objects.create_user(
        username='user1', email='u1@test.com', password='pw'
    )


def make_verse(user, interval_days=1):
    return MemorizeVerse.objects.create(
        user=user,
        book_id='GEN',
        book_name='Genesis',
        chapter=1,
        verse_number=1,
        translation='BSB',
        verse_text='In the beginning God created the heavens and the earth.',
        interval_days=interval_days,
    )


# score 0 reset to rung 0

class AdvanceScore0Test(TestCase):
    def setUp(self):
        self.user = make_user()

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_reset_from_rung0_is_noop(self, _):
        v = make_verse(self.user, interval_days=1)
        v.advance(0)
        self.assertEqual(v.interval_days, 1)
        self.assertEqual(v.next_review, FIXED_NOW + timedelta(days=1))

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_reset_from_rung2(self, _):
        v = make_verse(self.user, interval_days=7)
        v.advance(0)
        self.assertEqual(v.interval_days, 1)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_reset_from_off_ladder(self, _):
        v = make_verse(self.user, interval_days=28)
        v.advance(0)
        self.assertEqual(v.interval_days, 1)


# score 1 stay in place

class AdvanceScore1Test(TestCase):
    def setUp(self):
        self.user = make_user()

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_stay_on_ladder(self, _):
        v = make_verse(self.user, interval_days=3)
        v.advance(1)
        self.assertEqual(v.interval_days, 3)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_stay_off_ladder(self, _):
        v = make_verse(self.user, interval_days=28)
        v.advance(1)
        self.assertEqual(v.interval_days, 28)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_next_review_still_updated(self, _):
        v = make_verse(self.user, interval_days=3)
        v.advance(1)
        self.assertEqual(v.next_review, FIXED_NOW + timedelta(days=3))


# score 2 advance one rung

class AdvanceScore2Test(TestCase):
    def setUp(self):
        self.user = make_user()

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_rung0_to_rung1(self, _):
        v = make_verse(self.user, interval_days=1)
        v.advance(2)
        self.assertEqual(v.interval_days, 3)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_rung1_to_rung2(self, _):
        v = make_verse(self.user, interval_days=3)
        v.advance(2)
        self.assertEqual(v.interval_days, 7)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_rung2_to_rung3(self, _):
        v = make_verse(self.user, interval_days=7)
        v.advance(2)
        self.assertEqual(v.interval_days, 14)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_top_rung_doubles(self, _):
        v = make_verse(self.user, interval_days=14)
        v.advance(2)
        self.assertEqual(v.interval_days, 28)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_off_ladder_28_pins_to_top_then_doubles(self, _):
        # 28 not in ladder → pins to rung 3 doubles from 28 → 56
        v = make_verse(self.user, interval_days=28)
        v.advance(2)
        self.assertEqual(v.interval_days, 56)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_off_ladder_56_doubles_again(self, _):
        v = make_verse(self.user, interval_days=56)
        v.advance(2)
        self.assertEqual(v.interval_days, 112)


# score 3 advance one rung then double

class AdvanceScore3Test(TestCase):
    def setUp(self):
        self.user = make_user()

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_rung0(self, _):
        # 1 → advance to 3 ×2 = 6
        v = make_verse(self.user, interval_days=1)
        v.advance(3)
        self.assertEqual(v.interval_days, 6)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_rung1(self, _):
        # 3 → advance to 7 ×2 = 14
        v = make_verse(self.user, interval_days=3)
        v.advance(3)
        self.assertEqual(v.interval_days, 14)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_rung2(self, _):
        # 7 → advance to 14 ×2 = 28
        v = make_verse(self.user, interval_days=7)
        v.advance(3)
        self.assertEqual(v.interval_days, 28)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_top_rung_double_twice(self, _):
        # 14 → top rung doubles to 28 then ×2 = 56
        v = make_verse(self.user, interval_days=14)
        v.advance(3)
        self.assertEqual(v.interval_days, 56)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_off_ladder_28(self, _):
        # 28 off-ladder → pins to top 28×2=56 then ×2=112
        v = make_verse(self.user, interval_days=28)
        v.advance(3)
        self.assertEqual(v.interval_days, 112)


# side effects asserted on every call

class AdvanceSideEffectsTest(TestCase):
    def setUp(self):
        self.user = make_user()

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_rep_count_increments(self, _):
        v = make_verse(self.user, interval_days=1)
        v.advance(2)
        self.assertEqual(v.rep_count, 1)
        v.advance(2)
        self.assertEqual(v.rep_count, 2)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_last_score_recorded(self, _):
        v = make_verse(self.user, interval_days=1)
        v.advance(3)
        self.assertEqual(v.last_score, 3)

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_next_review_set_correctly(self, _):
        v = make_verse(self.user, interval_days=1)
        v.advance(2)  # → 3 days
        self.assertEqual(v.next_review, FIXED_NOW + timedelta(days=3))

    @patch('django.utils.timezone.now', return_value=FIXED_NOW)
    def test_changes_persisted_to_db(self, _):
        v = make_verse(self.user, interval_days=1)
        v.advance(2)
        fresh = MemorizeVerse.objects.get(pk=v.pk)
        self.assertEqual(fresh.interval_days, 3)
        self.assertEqual(fresh.rep_count, 1)
        self.assertEqual(fresh.last_score, 2)
