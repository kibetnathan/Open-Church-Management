from django.urls import path, include
from . import views
from .views import LeadershipTeamViewSet, ServicesViewSet, FellowshipGroupViewSet, CourseViewSet, DepartmentViewSet, EquipmentViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"leadership-team", LeadershipTeamViewSet)
router.register(r"services", ServicesViewSet)
router.register(r"fellowship-group", FellowshipGroupViewSet)
router.register(r"course", CourseViewSet)
router.register(r"department", DepartmentViewSet)
router.register(r"equipment", EquipmentViewSet)


urlpatterns= [
    path('home', views.home, name='home'),
    path("pastor/", views.PastorDashboardView.as_view(), name="pastor"),
    path("pastor/<str:view_type>/", views.PastorDashboardView.as_view(), name="pastor_view"),
    path('api/', include(router.urls)),
    path('not-authorized/', views.not_authorized, name='not_authorized'),
]