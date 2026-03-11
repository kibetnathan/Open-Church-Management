from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from taggit.utils import parse_tags
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-published_date')
    serializer_class = PostSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, published_date=timezone.now())

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('created_at')  # ← add this back
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = Comment.objects.all().order_by('created_at')
        post_id = self.request.query_params.get('post')
        if post_id:
            qs = qs.filter(post_id=post_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

def posts(request):
    return render(request, 'posts.html')

def posts_form(request):
    return render(request, 'postform.html')

@login_required
def create_post(request):
    if request.method == "POST":
        title = request.POST.get("title")
        text = request.POST.get("text")
        tags = request.POST.get("tags", "")
        image = request.FILES.get("image")  # handle uploaded image

        post = Post.objects.create(
            title=title,
            text=text,
            author=request.user,
            published_date=timezone.now(),
            image=image if image else None
        )

        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            post.tags.add(*tag_list)

        return redirect("posts")  # redirect somewhere

    return render(request, "postform.html")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    user = request.user

    if post.liked_by.filter(id=user.id).exists():
        post.liked_by.remove(user)
        liked = False
    else:
        post.liked_by.add(user)
        liked = True

    return Response({
        'liked': liked,
        'like_count': post.liked_by.count()
    })