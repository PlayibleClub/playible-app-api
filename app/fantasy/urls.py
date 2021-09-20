from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from . import views

router = DefaultRouter()
router.register(r'team', views.TeamViewSet)
router.register(r'positions', views.PositionViewSet)
router.register(r'contracts', views.ContractViewSet)
# router.register(r'athlete', views.AthleteViewSet)

urlpatterns = [
  url(r'', include(router.urls)),
]