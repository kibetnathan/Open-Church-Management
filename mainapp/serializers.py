from rest_framework import serializers
from .models import LeadershipTeam, Department, Course, Equipment, Services, FellowshipGroup, MemorizeVerse, MemorizationAttempt
from django.conf import settings
from userapp.models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'role']


class LeadershipTeamSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True
    )

    class Meta:
        model = LeadershipTeam
        fields = ['id', 'name', 'description', 'members']


class ServicesSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True
    )
    pastor = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),       allow_null=True
    )
    class Meta:
        model = Services
        fields = ['id', 'name', 'description', 'members', 'pastor']


class CourseSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True
    )
    leader = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        allow_null=True
    )

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'start_date', 'expected_duration', 'leader', 'members']


class FellowshipGroupSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True
    )
    leader = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        allow_null=True
    )

    class Meta:
        model = FellowshipGroup
        fields = ['id', 'name', 'description', 'leader' ,'members']


class DepartmentSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True
    )
    leader = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        allow_null=True
    )

    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'leader' ,'members']


class EquipmentSerializer(serializers.ModelSerializer):
    assigned_service = serializers.PrimaryKeyRelatedField(
        queryset=Services.objects.all(),
        allow_null=True
    )
    assigned_department = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        allow_null=True
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Equipment
        fields = ['id', 'name', 'image', 'description', 'quantity', 'assigned_service', 'assigned_department']


class MemorizationAttemptSerializer(serializers.ModelSerializer):
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    score_display = serializers.CharField(source='get_score_display', read_only=True)

    class Meta:
        model = MemorizationAttempt
        fields = [
            'id',
            'attempted_at',
            'level',
            'level_display',
            'score',
            'score_display',
        ]
        read_only_fields = ['id', 'attempted_at']


class MemorizeVerseSerializer(serializers.ModelSerializer):
    """Full serializer — used for list and retrieve."""
    is_due = serializers.BooleanField(read_only=True)
    reference = serializers.CharField(read_only=True)
    recent_attempts = serializers.SerializerMethodField()

    class Meta:
        model = MemorizeVerse
        fields = [
            'id',
            'book_id',
            'book_name',
            'chapter',
            'verse_number',
            'translation',
            'verse_text',
            'next_review',
            'interval_days',
            'rep_count',
            'last_score',
            'added_at',
            'is_due',
            'reference',
            'recent_attempts',
        ]
        read_only_fields = [
            'id',
            'next_review',
            'interval_days',
            'rep_count',
            'last_score',
            'added_at',
        ]

    def get_recent_attempts(self, obj):
        # Last 5 attempts — enough for a streak indicator on the frontend
        attempts = obj.attempts.all()[:5]
        return MemorizationAttemptSerializer(attempts, many=True).data


class MemorizeVerseCreateSerializer(serializers.ModelSerializer):
    """
    Slim serializer for the bookmark action.
    The frontend sends the reference + cached verse text;
    we attach the user in the viewset.
    """

    class Meta:
        model = MemorizeVerse
        fields = [
            'book_id',
            'book_name',
            'chapter',
            'verse_number',
            'translation',
            'verse_text',
        ]

    def validate(self, attrs):
        user = self.context['request'].user
        already_exists = MemorizeVerse.objects.filter(
            user=user,
            book_id=attrs['book_id'],
            chapter=attrs['chapter'],
            verse_number=attrs['verse_number'],
            translation=attrs['translation'],
        ).exists()
        if already_exists:
            raise serializers.ValidationError(
                'You have already saved this verse.'
            )
        return attrs


class ReviewSerializer(serializers.Serializer):
    """
    Payload for POST /memorize/{id}/review/
    Validates the score and level submitted after a practice session.
    """
    score = serializers.IntegerField(min_value=0, max_value=3)
    level = serializers.IntegerField(min_value=1, max_value=4)