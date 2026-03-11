from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import LeadershipTeam, Services, Department, FellowshipGroup, Course, Equipment
from .serializers import LeadershipTeamSerializer, ServicesSerializer, DepartmentSerializer,FellowshipGroupSerializer, CourseSerializer, EquipmentSerializer
from communication.models import Post
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .mixins import PastorRequiredMixin, PastorContextMixin

def is_pastor(user):
    return user.groups.filter(name='Pastors').exists()

def index(request):
    return render(request, 'index.html')


class PastorDashboardView(LoginRequiredMixin, PastorRequiredMixin, PastorContextMixin, TemplateView):
    template_name = "pastor.html"  # default template

    def get_template_names(self):
        """
        Switch template based on URL or query param.
        """
        view_type = self.kwargs.get("view_type", "home")  # default to 'home'
        if view_type == "general":
            return ["dashboards/pastors/general.html"]
        elif view_type == "services": 
            return ["dashboards/pastors/services.html"]
        return ["pastor.html"]

def not_authorized(request):
    return render(request, 'unauthorized.html')

@login_required
def home(request):
    return render(request, 'home.html')

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
