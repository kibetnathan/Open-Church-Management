from rest_framework import serializers
from .models import LeadershipTeam, Department, Course, Equipment, Services, FellowshipGroup
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

# class MinistryDataSerializer(serializers.ModelSerializer):
#     # Nested user info
#     user = UserSerializer(read_only=True)
#     # Computed properties
#     name = serializers.CharField(source='name', read_only=True)
#     campus = serializers.CharField(source='campus', read_only=True)
#     # Nested or IDs for relations
#     dg = DiscipleshipGroupSerializer(read_only=True)
#     department = ServingTeamSerializer(many=True, read_only=True)

#     # For writable operations (POST/PUT), use PrimaryKeyRelatedField
#     user_id = serializers.PrimaryKeyRelatedField(
#         queryset=CustomUser.objects.all(), source='user', write_only=True
#     )
#     dg_id = serializers.PrimaryKeyRelatedField(
#         queryset=DiscipleshipGroup.objects.all(), source='dg', write_only=True, allow_null=True
#     )
#     department_ids = serializers.PrimaryKeyRelatedField(
#         queryset=ServingTeam.objects.all(),
#         many=True,
#         source='department',
#         write_only=True,
#         required=False
#     )

#     class Meta:
#         model = MinistryData
#         fields = [
#             'id', 'user', 'user_id', 'name', 'campus', 'dg', 'dg_id', 'department', 'department_ids'
#         ]