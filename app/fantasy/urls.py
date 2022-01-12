from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from . import views

router = DefaultRouter()
router.register(r'team', views.TeamViewSet)
router.register(r'athlete', views.CreateAthleteViewSet)
router.register(r'athleteseason', views.AthleteSeasonViewSet)

urlpatterns = [
  url(r'', include(router.urls)),
]