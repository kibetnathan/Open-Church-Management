from rest_framework import serializers
from .models import Post, Comment
from userapp.models import CustomUser
from userapp.serializers import UserSerializer, ProfileSerializer
from taggit.serializers import (TagListSerializerField, TaggitSerializer)

class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    author_profile = serializers.SerializerMethodField()
    # Use a basic ListField of Strings. No specialized taggit fields!
    tags = serializers.CharField(required=False, allow_blank=True)
    image = serializers.ImageField(required=False, allow_null=True)
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            'id', 'image', 'title', 'text', 'published_date', 
            'author', 'tags', 'like_count', 'is_liked', 
            'author_profile', 'comment_count'
        ]

    def get_author_profile(self, obj):
        profile = obj.author.profile
        return ProfileSerializer(profile).data if profile else None

    def to_representation(self, instance):
        """
        This converts the tags BACK into a list when sending data TO React,
        so your frontend still sees ["tag1", "tag2"].
        """
        representation = super().to_representation(instance)
        representation['tags'] = [tag.name for tag in instance.tags.all()]
        return representation

    def create(self, validated_data):
        # 2. Extract the raw string "tags, tags"
        tags_string = validated_data.pop('tags', '')
        
        # Create the post
        post = Post.objects.create(**validated_data)
        
        # 3. Split and add the tags manually
        if tags_string:
            tag_list = [t.strip() for t in tags_string.split(',') if t.strip()]
            post.tags.add(*tag_list)
            
        return post

    def update(self, instance, validated_data):
        tags_string = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        
        if tags_string is not None:
            tag_list = [t.strip() for t in tags_string.split(',') if t.strip()]
            instance.tags.set(*tag_list)
            
        return instance
    # ... keep your other get_ methods (like_count, etc.) ...
    def get_like_count(self, obj):
        return obj.liked_by.count()
    def get_comment_count(self, obj):
        return obj.post_comments.count()
    def get_is_liked(self, obj):
        user = self.context.get('request').user
        if user.is_authenticated:
            return obj.liked_by.filter(id=user.id).exists()
        return False
class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)          # nested object, not just username
    author_profile = serializers.SerializerMethodField()
    post_id = serializers.PrimaryKeyRelatedField(
        queryset=Post.objects.all(),
        source='post',
        write_only=True
    )

    class Meta:
        model = Comment
        fields = ['id', 'post_id', 'text', 'created_at', 'author', 'author_profile']

    def get_author_profile(self, obj):
        try:
            profile = obj.author.profile
            return ProfileSerializer(profile).data if profile else None
        except Exception:
            return None