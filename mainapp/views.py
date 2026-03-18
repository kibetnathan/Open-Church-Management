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
