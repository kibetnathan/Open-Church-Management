from django.urls import path, include
from .views import LeadershipTeamViewSet, ServicesViewSet, FellowshipGroupViewSet, CourseViewSet, DepartmentViewSet, EquipmentViewSet, MemorizeVerseViewSet, MemorizationAttemptViewSet, ReadingPlanViewSet, CharityOrganisationViewSet
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"leadership-team", LeadershipTeamViewSet)
router.register(r"services", ServicesViewSet)
router.register(r"fellowship-group", FellowshipGroupViewSet)
router.register(r"course", CourseViewSet)
router.register(r"department", DepartmentViewSet)
router.register(r"equipment", EquipmentViewSet)
router.register(r'memorize', MemorizeVerseViewSet, basename='memorize-verse')
router.register(r'memorize/attempts', MemorizationAttemptViewSet, basename='memorize-attempt')
router.register(r'reading-plans', ReadingPlanViewSet, basename='reading-plan')
router.register(r'charity-organisations', CharityOrganisationViewSet, basename='charity-organisation')


urlpatterns= [
    path('api/', include(router.urls)),
]