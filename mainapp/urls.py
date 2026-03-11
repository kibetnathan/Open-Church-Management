from django.urls import path, include
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
    path('api/', include(router.urls)),
]