from django.test import TestCase
from rest_framework.test import APIClient

from userapp.models import CustomUser
from mainapp.models import FellowshipGroup, Department, ReadingPlan, ReadingPlanMember

LIST_URL = '/api/reading-plans/'
MY_URL = '/api/reading-plans/my/'


def make_user(username):
    return CustomUser.objects.create_user(
        username=username, email=f'{username}@test.com', password='pw'
    )


def make_plan(title, is_active=True):
    return ReadingPlan.objects.create(
        title=title,
        youversion_url='https://www.bible.com/reading-plans/1234',
        is_active=is_active,
    )


def plan_ids_for(client, user):
    client.force_authenticate(user)
    resp = client.get(LIST_URL)
    assert resp.status_code == 200
    data = resp.data
    results = data['results'] if isinstance(data, dict) else data
    return {p['id'] for p in results}


# ── Visibility ────────────────────────────────────────────────────────────────

class ReadingPlanVisibilityTest(TestCase):
    def setUp(self):
        self.client = APIClient()

        leader = make_user('leader')
        self.fg1 = FellowshipGroup.objects.create(
            name='FG1', description='', leader=leader
        )
        self.dept1 = Department.objects.create(
            name='Dept1', description='', leader=leader
        )

        self.user_fg = make_user('user_fg')
        self.fg1.members.add(self.user_fg)

        self.user_dept = make_user('user_dept')
        self.dept1.members.add(self.user_dept)

        self.user_unaffiliated = make_user('user_unaffiliated')

        self.user_multi = make_user('user_multi')
        self.fg1.members.add(self.user_multi)
        self.dept1.members.add(self.user_multi)

        self.p_churchwide = make_plan('P_churchwide')

        self.p_inactive = make_plan('P_inactive', is_active=False)

        self.p_fg = make_plan('P_fg')
        self.p_fg.fellowship_groups.add(self.fg1)

        self.p_dept = make_plan('P_dept')
        self.p_dept.departments.add(self.dept1)

        self.p_multi_scope = make_plan('P_multi_scope')
        self.p_multi_scope.fellowship_groups.add(self.fg1)
        self.p_multi_scope.departments.add(self.dept1)

    def test_churchwide_visible_to_all_users(self):
        for user in [self.user_fg, self.user_dept, self.user_unaffiliated, self.user_multi]:
            self.assertIn(
                self.p_churchwide.id, plan_ids_for(self.client, user),
                f'{user.username} should see P_churchwide'
            )

    def test_inactive_plan_visible_to_nobody(self):
        for user in [self.user_fg, self.user_dept, self.user_unaffiliated, self.user_multi]:
            self.assertNotIn(
                self.p_inactive.id, plan_ids_for(self.client, user),
                f'{user.username} should not see P_inactive'
            )

    def test_fg_plan_visible_to_fg_member_only(self):
        self.assertIn(self.p_fg.id, plan_ids_for(self.client, self.user_fg))
        self.assertNotIn(self.p_fg.id, plan_ids_for(self.client, self.user_dept))
        self.assertNotIn(self.p_fg.id, plan_ids_for(self.client, self.user_unaffiliated))

    def test_dept_plan_visible_to_dept_member_only(self):
        self.assertIn(self.p_dept.id, plan_ids_for(self.client, self.user_dept))
        self.assertNotIn(self.p_dept.id, plan_ids_for(self.client, self.user_fg))
        self.assertNotIn(self.p_dept.id, plan_ids_for(self.client, self.user_unaffiliated))

    def test_multi_scope_uses_or_logic(self):
        self.assertIn(self.p_multi_scope.id, plan_ids_for(self.client, self.user_fg))
        self.assertIn(self.p_multi_scope.id, plan_ids_for(self.client, self.user_dept))
        self.assertNotIn(self.p_multi_scope.id, plan_ids_for(self.client, self.user_unaffiliated))

    def test_fg_user_sees_both_churchwide_and_scoped_plan(self):
        ids = plan_ids_for(self.client, self.user_fg)
        self.assertIn(self.p_churchwide.id, ids)
        self.assertIn(self.p_fg.id, ids)

    def test_no_duplicates_for_multi_group_member(self):
        self.client.force_authenticate(self.user_multi)
        resp = self.client.get(LIST_URL)
        data = resp.data
        results = data['results'] if isinstance(data, dict) else data
        ids = [p['id'] for p in results]
        self.assertEqual(ids.count(self.p_multi_scope.id), 1)


# ── Join / Leave ──────────────────────────────────────────────────────────────

class ReadingPlanJoinLeaveTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user('user1')
        self.user2 = make_user('user2')
        self.plan = make_plan('Test Plan')

    def _join(self, user=None):
        self.client.force_authenticate(user or self.user)
        return self.client.post(f'/api/reading-plans/{self.plan.pk}/join/')

    def _leave(self, user=None):
        self.client.force_authenticate(user or self.user)
        return self.client.post(f'/api/reading-plans/{self.plan.pk}/leave/')

    def test_first_join_creates_membership(self):
        resp = self._join()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['created'])
        self.assertEqual(resp.data['member_count'], 1)
        self.assertEqual(ReadingPlanMember.objects.filter(plan=self.plan).count(), 1)

    def test_second_join_is_idempotent(self):
        self._join()
        resp = self._join()
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.data['created'])
        self.assertEqual(resp.data['member_count'], 1)

    def test_leave_after_join_removes_membership(self):
        self._join()
        resp = self._leave()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['member_count'], 0)
        self.assertFalse(
            ReadingPlanMember.objects.filter(plan=self.plan, user=self.user).exists()
        )

    def test_leave_without_joining_is_silent_noop(self):
        resp = self._leave()
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['member_count'], 0)

    def test_rejoin_after_leave_creates_fresh_membership(self):
        self._join()
        self._leave()
        resp = self._join()
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data['created'])
        self.assertEqual(resp.data['member_count'], 1)

    def test_two_different_users_join_same_plan(self):
        self._join(self.user)
        self._join(self.user2)
        self.client.force_authenticate(self.user)
        resp = self.client.get(f'/api/reading-plans/{self.plan.pk}/')
        self.assertEqual(resp.data['member_count'], 2)

    def test_my_returns_only_joined_plans(self):
        other = make_plan('Other Plan')
        self._join()  # join self.plan only
        self.client.force_authenticate(self.user)
        resp = self.client.get(MY_URL)
        self.assertEqual(resp.status_code, 200)
        ids = [p['id'] for p in resp.data]
        self.assertIn(self.plan.id, ids)
        self.assertNotIn(other.id, ids)

    def test_unauthenticated_join_is_rejected(self):
        resp = self.client.post(f'/api/reading-plans/{self.plan.pk}/join/')
        self.assertIn(resp.status_code, (401, 403))

    def test_unauthenticated_leave_is_rejected(self):
        resp = self.client.post(f'/api/reading-plans/{self.plan.pk}/leave/')
        self.assertIn(resp.status_code, (401, 403))
