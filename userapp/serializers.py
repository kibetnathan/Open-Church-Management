from rest_framework import serializers
from .models import CustomUser, Profile
from datetime import date 
from django.contrib.auth.models import Group
from cloudinary.models import CloudinaryField

class UserSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True
    )
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'groups']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        source='user',
        write_only=True
    )
    # Read: returns the URL string
    profile_pic_url = serializers.SerializerMethodField()
    # Write: accepts the uploaded file
    profile_pic = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'user_id', 'age', 'DoB',
            'school', 'workplace', 'phone_number', 'campus',
            'profile_pic',      # writable upload field
            'profile_pic_url',  # read-only URL
        ]
        read_only_fields = ["user"]

    def get_profile_pic_url(self, obj):
        if obj.profile_pic:
            return obj.profile_pic.url
        return None

    def validate_age(self, value):
        if value < 0:
            raise serializers.ValidationError("Age cannot be negative")
        if value > 120:
            raise serializers.ValidationError("Age seems unrealistically high")
        return value

    def validate_DoB(self, value):
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future")
        return value
    
class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "name"]