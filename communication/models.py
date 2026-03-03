from django.db import models
from cloudinary.models import CloudinaryField
from django.conf import settings
from taggit.managers import TaggableManager

# Create your models here.
class Post(models.Model):
    image = CloudinaryField("image", null=True, blank=True)
    title = models.CharField(max_length=100)
    text = models.TextField()
    published_date = models.DateTimeField(blank=True, null=True)
    liked_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='liked_posts')
    # comments = models.ManyToManyField('Comment', blank=True, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    tags = TaggableManager()

    def __str__(self):
        return self.title
    
class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="post_comments"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return (f"Comment by {self.author}, {self.text[:30]}")
    
class Thread(models.Model):
    image = CloudinaryField("image", null=True, blank=True)
    title = models.CharField(max_length=100)
    text = models.TextField()
    published_date = models.DateTimeField(blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    def __str__(self):
        return self.title
    
class Replies(models.Model):
    thread = models.ForeignKey(
        Thread,
        on_delete=models.CASCADE,
        related_name="thread_reply"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return (f"Reply by {self.author}, {self.text[:30]}")