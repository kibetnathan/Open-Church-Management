from django.contrib.auth.mixins import UserPassesTestMixin
from communication.models import Post
from userapp.models import CustomUser, Profile
from mainapp.models import FellowshipGroup, Services, Department, Course
from django.db.models import Count


class PastorRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.groups.filter(name="Pastor").exists()

    def handle_no_permission(self):
        from django.shortcuts import redirect
        return redirect("/not-authorized/")


class PastorContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "posts": Post.objects.annotate(like_count=Count("liked_by")).order_by("-like_count")[:5],
            "leaders": CustomUser.objects.filter(groups__name__in=["Head Pastor","Pastor", "Leader", "Jr Leader"]).distinct(),
            "services": Services.objects.annotate(member_count=Count("members")).order_by("-member_count")[:5],
            "scriptures":{
                "John 3:16": "For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.",
                "Psalm 23:1": "The Lord is my shepherd, I lack nothing.",
                "Philippians 4:13": "I can do all this through him who gives me strength.",
                "Romans 8:28": "And we know that in all things God works for the good of those who love him, who have been called according to his purpose."
            },
            "my_services": Services.objects.filter(pastor=self.request.user).annotate(member_count=Count("members")).order_by("-member_count")[:5],
        })
        return context
