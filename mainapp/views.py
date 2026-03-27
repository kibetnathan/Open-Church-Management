import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, BasePermission
from django.utils import timezone
from django.db.models import Q
from .models import LeadershipTeam, Services, Department, FellowshipGroup, Course, Equipment, MemorizeVerse, MemorizationAttempt, ReadingPlan, ReadingPlanMember, CharityOrganisation
from .serializers import LeadershipTeamSerializer, ServicesSerializer, DepartmentSerializer, FellowshipGroupSerializer, CourseSerializer, EquipmentSerializer, MemorizeVerseSerializer, MemorizeVerseCreateSerializer, MemorizationAttemptSerializer, ReviewSerializer, ReadingPlanSerializer, ReadingPlanCreateSerializer, CharityOrganisationSerializer


def is_pastor(user):
    return user.groups.filter(name='Pastors').exists()


class LeadershipTeamViewSet(viewsets.ModelViewSet):
    queryset = LeadershipTeam.objects.all().order_by('id')
    serializer_class = LeadershipTeamSerializer

class ServicesViewSet(viewsets.ModelViewSet):
    queryset = Services.objects.all().order_by('id')
    serializer_class = ServicesSerializer

class FellowshipGroupViewSet(viewsets.ModelViewSet):
    queryset = FellowshipGroup.objects.all().order_by('id')
    serializer_class = FellowshipGroupSerializer

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('id')
    serializer_class = CourseSerializer

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all().order_by('id')
    serializer_class = DepartmentSerializer

class EquipmentViewSet(viewsets.ModelViewSet):
    queryset = Equipment.objects.all().order_by('id')
    serializer_class = EquipmentSerializer


class MemorizeVerseViewSet(viewsets.ModelViewSet):
    """
    CRUD for a user's saved verses + review action.

    Routes (assuming router prefix 'memorize/'):
        GET     /memorize/              — list all saved verses
        POST    /memorize/              — bookmark a new verse
        GET     /memorize/{id}/         — retrieve one verse
        DELETE  /memorize/{id}/         — remove from queue
        GET     /memorize/due/          — verses due for review today
        POST    /memorize/{id}/review/  — submit a practice result
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            MemorizeVerse.objects
            .filter(user=self.request.user)
            .prefetch_related('attempts')
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return MemorizeVerseCreateSerializer
        return MemorizeVerseSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='due')
    def due(self, request):
        """Return all verses whose next_review is now or in the past."""
        due_verses = self.get_queryset().filter(next_review__lte=timezone.now())
        serializer = MemorizeVerseSerializer(due_verses, many=True)
        return Response({
            'count': due_verses.count(),
            'results': serializer.data,
        })

    @action(detail=True, methods=['post'], url_path='review')
    def review(self, request, pk=None):
        """
        Submit a review result for a single verse.

        Expects: { "score": 0-3, "level": 1-4 }
        """
        verse = self.get_object()

        review_serializer = ReviewSerializer(data=request.data)
        review_serializer.is_valid(raise_exception=True)

        score = review_serializer.validated_data['score']
        level = review_serializer.validated_data['level']

        MemorizationAttempt.objects.create(
            verse=verse,
            score=score,
            level=level,
        )

        verse.advance(score)

        return Response(
            MemorizeVerseSerializer(verse).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Lightweight summary for a dashboard card."""
        from datetime import timedelta

        qs = self.get_queryset()
        total = qs.count()
        due_today = qs.filter(next_review__lte=timezone.now()).count()
        mastered = qs.filter(interval_days__gte=14).count()

        thirty_days_ago = timezone.now() - timedelta(days=30)
        attempt_days = (
            MemorizationAttempt.objects
            .filter(
                verse__user=request.user,
                attempted_at__gte=thirty_days_ago,
            )
            .dates('attempted_at', 'day')
        )

        streak = 0
        check_date = timezone.now().date()
        attempt_day_set = set(attempt_days)

        for _ in range(30):
            if check_date in attempt_day_set:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        return Response({
            'total': total,
            'due_today': due_today,
            'mastered': mastered,
            'streak': streak,
        })


class MemorizationAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only history of all attempts for the requesting user.
    Attempts are created via MemorizeVerseViewSet.review — not directly here.

    Routes (assuming router prefix 'memorize/attempts/'):
        GET  /memorize/attempts/           — full history
        GET  /memorize/attempts/{id}/      — single attempt
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MemorizationAttemptSerializer

    def get_queryset(self):
        return (
            MemorizationAttempt.objects
            .filter(verse__user=self.request.user)
            .select_related('verse')
        )


# ── Permissions ────────────────────────────────────────────────────────────────

class IsLeaderOrReadOnly(BasePermission):
    """
    Any authenticated user can read.
    Only users in a recognised leader group can create / update / delete.
    """
    LEADER_GROUPS = {
        'Pastor',
        'Leader',
        'DG Leader',
        'Department Leader',
        'Course Leader',
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        user_groups = set(request.user.groups.values_list('name', flat=True))
        return bool(user_groups & self.LEADER_GROUPS) or request.user.is_staff

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        user_groups = set(request.user.groups.values_list('name', flat=True))
        return bool(user_groups & self.LEADER_GROUPS) or request.user.is_staff


# ── ViewSet ────────────────────────────────────────────────────────────────────

class CharityOrganisationViewSet(viewsets.ModelViewSet):
    queryset = CharityOrganisation.objects.all().order_by('id')
    serializer_class = CharityOrganisationSerializer
    permission_classes = [IsLeaderOrReadOnly]


class ReadingPlanViewSet(viewsets.ModelViewSet):
    """
    Routes (router prefix 'reading-plans/'):

        GET    /reading-plans/              list plans visible to the user
        POST   /reading-plans/              create a plan (leaders only)
        GET    /reading-plans/{id}/         retrieve one plan
        PATCH  /reading-plans/{id}/         update (leaders only)
        DELETE /reading-plans/{id}/         delete (leaders only)
        POST   /reading-plans/{id}/join/    join a plan
        POST   /reading-plans/{id}/leave/   leave a plan
        GET    /reading-plans/my/           plans the user has joined
    """

    permission_classes = [IsLeaderOrReadOnly]

    def get_permissions(self):
        if self.action in ('join', 'leave', 'my', 'list', 'retrieve'):
            return [IsAuthenticated()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ReadingPlanCreateSerializer
        return ReadingPlanSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return ReadingPlan.objects.none()

        fellowship_ids = user.discipleship_group.values_list('id', flat=True)
        department_ids = user.serving_team.values_list('id', flat=True)
        course_ids     = user.ropes_class.values_list('id', flat=True)

        return ReadingPlan.objects.filter(
            is_active=True
        ).filter(
            Q(
                fellowship_groups__isnull=True,
                departments__isnull=True,
                courses__isnull=True,
            ) |
            Q(fellowship_groups__in=fellowship_ids) |
            Q(departments__in=department_ids) |
            Q(courses__in=course_ids)
        ).distinct().prefetch_related(
            'fellowship_groups', 'departments', 'courses', 'memberships'
        ).select_related('created_by')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='join')
    def join(self, request, pk=None):
        plan = self.get_object()
        _, created = ReadingPlanMember.objects.get_or_create(
            user=request.user, plan=plan
        )
        return Response(
            {
                'joined': True,
                'created': created,
                'member_count': ReadingPlanMember.objects.filter(plan=plan).count(),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='leave')
    def leave(self, request, pk=None):
        plan = self.get_object()
        ReadingPlanMember.objects.filter(
            user=request.user, plan=plan
        ).delete()
        return Response(
            {
                'joined': False,
                'member_count': ReadingPlanMember.objects.filter(plan=plan).count(),
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='my')
    def my(self, request):
        """Return plans the current user has explicitly joined."""
        joined_ids = ReadingPlanMember.objects.filter(
            user=request.user
        ).values_list('plan_id', flat=True)
        plans = self.get_queryset().filter(id__in=joined_ids)
        serializer = ReadingPlanSerializer(plans, many=True, context={'request': request})
        return Response(serializer.data)

class VerifyPaymentView(APIView):
    def post(self, request):
        reference = request.data.get('reference')
        
        if not reference:
            return Response({"error": "No reference provided"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Prepare the Paystack Verification URL
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        # 2. Call Paystack API
        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()

            # 3. Check if the transaction was successful
            if response_data['status'] and response_data['data']['status'] == 'success':
                # CRITICAL: Verify the amount matches your database record!
                amount_paid = response_data['data']['amount'] # in subunits (e.g. Kobo/Cents)
                
                # Logic: Update your Order model
                # order = Order.objects.get(id=reference)
                # order.paid = True
                # order.save()

                return Response({"status": "verified", "detail": "Payment successful"}, status=status.HTTP_200_OK)
            
            return Response({"status": "failed", "detail": "Transaction not successful"}, status=status.HTTP_400_BAD_REQUEST)

        except requests.exceptions.RequestException as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
