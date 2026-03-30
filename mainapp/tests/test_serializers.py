from django.test import TestCase
from rest_framework.test import APIClient

from userapp.models import CustomUser
from mainapp.models import MemorizeVerse, ReadingPlan

MEMORIZE_URL = '/api/memorize/'
PLANS_URL = '/api/reading-plans/'

VERSE_PAYLOAD = {
    'book_id': 'GEN',
    'book_name': 'Genesis',
    'chapter': 1,
    'verse_number': 1,
    'translation': 'BSB',
    'verse_text': 'In the beginning God created the heavens and the earth.',
}


def make_user(username):
    return CustomUser.objects.create_user(
        username=username, email=f'{username}@test.com', password='pw'
    )


# duplicate verse check

class DuplicateVerseTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user('user1')
        self.user2 = make_user('user2')

    def test_duplicate_returns_400(self):
        self.client.force_authenticate(self.user)
        self.client.post(MEMORIZE_URL, VERSE_PAYLOAD, format='json')
        resp = self.client.post(MEMORIZE_URL, VERSE_PAYLOAD, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('already saved', str(resp.data))

    def test_different_translation_is_allowed(self):
        self.client.force_authenticate(self.user)
        self.client.post(MEMORIZE_URL, VERSE_PAYLOAD, format='json')
        resp = self.client.post(
            MEMORIZE_URL, {**VERSE_PAYLOAD, 'translation': 'KJV'}, format='json'
        )
        self.assertEqual(resp.status_code, 201)

    def test_different_user_is_allowed(self):
        self.client.force_authenticate(self.user)
        self.client.post(MEMORIZE_URL, VERSE_PAYLOAD, format='json')
        self.client.force_authenticate(self.user2)
        resp = self.client.post(MEMORIZE_URL, VERSE_PAYLOAD, format='json')
        self.assertEqual(resp.status_code, 201)

    def test_different_chapter_is_allowed(self):
        self.client.force_authenticate(self.user)
        self.client.post(MEMORIZE_URL, VERSE_PAYLOAD, format='json')
        resp = self.client.post(
            MEMORIZE_URL, {**VERSE_PAYLOAD, 'chapter': 2}, format='json'
        )
        self.assertEqual(resp.status_code, 201)


# youversion url validation

PLAN_BASE = {
    'title': 'Test Plan',
    'description': '',
    'fellowship_groups': [],
    'departments': [],
    'courses': [],
}


class YouVersionURLValidationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user('staff')
        self.user.is_staff = True
        self.user.save()
        self.client.force_authenticate(self.user)

    def _post(self, url):
        return self.client.post(
            PLANS_URL, {**PLAN_BASE, 'youversion_url': url}, format='json'
        )

    def test_valid_base_url(self):
        resp = self._post('https://www.bible.com/reading-plans/1234')
        self.assertEqual(resp.status_code, 201)

    def test_valid_url_with_extra_path_segments(self):
        resp = self._post('https://www.bible.com/reading-plans/1234/day/1')
        self.assertEqual(resp.status_code, 201)

    def test_invalid_no_plan_id(self):
        resp = self._post('https://www.bible.com/reading-plans/')
        self.assertEqual(resp.status_code, 400)

    def test_invalid_wrong_path_keyword(self):
        resp = self._post('https://www.bible.com/plans/1234')
        self.assertEqual(resp.status_code, 400)

    def test_invalid_letters_instead_of_digits(self):
        resp = self._post('https://www.bible.com/reading-plans/abc')
        self.assertEqual(resp.status_code, 400)

    def test_other_domain_passes_path_only_regex(self):
        # Known loose behavior regex only checks the path not the domain
        resp = self._post('https://other-site.com/reading-plans/1234')
        self.assertEqual(resp.status_code, 201)


# readingplan computed properties

class ReadingPlanPropertiesTest(TestCase):
    def setUp(self):
        self.plan = ReadingPlan(
            title='Test',
            youversion_url='https://www.bible.com/reading-plans/9876',
        )

    def test_youversion_plan_id_extracted(self):
        self.assertEqual(self.plan.youversion_plan_id, '9876')

    def test_widget_url_constructed(self):
        self.assertEqual(
            self.plan.widget_url,
            'https://www.bible.com/widgets/reading-plans/9876',
        )
