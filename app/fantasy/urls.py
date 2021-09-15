from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from . import views

router = DefaultRouter()
router.register(r'fantasy', views.TeamViewSet)

urlpatterns = [
  url(r'', include(router.urls)),
]