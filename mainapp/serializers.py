from rest_framework import serializers
from .models import LeadershipTeam, Department, Course, Equipment, Services, FellowshipGroup, MemorizeVerse, MemorizationAttempt, ReadingPlan, CharityOrganisation
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
        # Last 5 attempts enough for a streak indicator on the frontend
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


class ReadingPlanSerializer(serializers.ModelSerializer):
    youversion_plan_id = serializers.CharField(read_only=True)
    widget_url         = serializers.CharField(read_only=True)
    is_church_wide     = serializers.BooleanField(read_only=True)
    member_count       = serializers.SerializerMethodField()
    is_joined          = serializers.SerializerMethodField()
    created_by_name    = serializers.SerializerMethodField()

    class Meta:
        model = ReadingPlan
        fields = [
            'id',
            'title',
            'description',
            'youversion_url',
            'youversion_plan_id',
            'widget_url',
            'cover_image',
            'start_date',
            'duration_days',
            'is_active',
            'is_church_wide',
            'fellowship_groups',
            'departments',
            'courses',
            'member_count',
            'is_joined',
            'created_by',
            'created_by_name',
            'created_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at']

    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_is_joined(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.memberships.filter(user=request.user).exists()

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username
        return None

    def validate_youversion_url(self, value):
        import re
        if not re.search(r'/reading-plans/(\d+)', value):
            raise serializers.ValidationError(
                "Must be a valid YouVersion URL containing a plan ID, "
                "e.g. https://www.bible.com/reading-plans/1234"
            )
        return value


class CharityOrganisationSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        many=True,
        required=False,
    )
    pastor = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        allow_null=True,
    )
    banner = serializers.ImageField(required=False, allow_null=True)
    class Meta:
        model = CharityOrganisation
        fields = [
            'id',
            'name',
            'description',
            'banner',
            'payment_method',
            'donation_link',
            'pastor',
            'members',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ReadingPlanCreateSerializer(ReadingPlanSerializer):
    """
    Used for POST/PATCH — exposes M2M fields as writable ID lists.
    created_by is injected by the viewset, not sent by the client.
    """
    class Meta(ReadingPlanSerializer.Meta):
        read_only_fields = ['id', 'created_by', 'created_at']