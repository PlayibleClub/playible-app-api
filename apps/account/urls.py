from django.urls import path, include
from django.conf.urls import url

from rest_framework.routers import DefaultRouter

from apps.account.views import *

router = DefaultRouter()
router.register(r'collections', CollectionViewSet)
router.register(r'accounts', AccountViewset)
router.register(r'assets', AssetViewset)
router.register(r'sales', SalesOrderViewset)
router.register(r'emails', EmailViewset)

urlpatterns = [
    url(r'', include(router.urls)),
    path('athlete_tokens/<str:wallet>/collection/<str:contract>', AthleteTokenView.as_view()),
]
