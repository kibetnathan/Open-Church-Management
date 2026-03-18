from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import LeadershipTeam, Services, Department, FellowshipGroup, Course, Equipment, MemorizeVerse, MemorizationAttempt
from .serializers import LeadershipTeamSerializer, ServicesSerializer, DepartmentSerializer,FellowshipGroupSerializer, CourseSerializer, EquipmentSerializer, MemorizeVerseSerializer, MemorizeVerseCreateSerializer, MemorizationAttemptSerializer, ReviewSerializer


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
