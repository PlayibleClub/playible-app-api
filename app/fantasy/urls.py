from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from . import views

router = DefaultRouter()
router.register(r'team', views.TeamViewSet)
router.register(r'positions', views.PositionViewSet)
router.register(r'athlete', views.AthleteViewSet)
router.register(r'contracts', views.ContractViewSet)
router.register(r'accounts', views.AccountViewset)
router.register(r'assets', views.AssetViewset)

urlpatterns = [
  url(r'', include(router.urls)),
]