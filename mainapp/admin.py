from django.contrib import admin
from .models import LeadershipTeam, FellowshipGroup, Services, Department, Course, Equipment
@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name', 'pastor')
    filter_horizontal = ('members',)  # nice multi-select for members

@admin.register(FellowshipGroup)
class FellowshipGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader')
    filter_horizontal = ('members',)

@admin.register(LeadershipTeam)
class LeadershipTeamAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('members',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    filter_horizontal = ('members',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader')
    filter_horizontal = ('members',)

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'assigned_service', 'assigned_department')