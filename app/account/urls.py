from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from . import views

router = DefaultRouter()
router.register(r'collections', views.CollectionViewSet)
router.register(r'accounts', views.AccountViewset)
router.register(r'assets', views.AssetViewset)
router.register(r'sales', views.SalesOrderViewset)
router.register(r'emails', views.EmailViewset)

urlpatterns = [
  url(r'', include(router.urls)),
]