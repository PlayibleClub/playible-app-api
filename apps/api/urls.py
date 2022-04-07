from django.urls import re_path, include


urlpatterns = [
    re_path(r'^mlb/', include(('apps.api.mlb.urls', 'mlb'), namespace='mlb')),
]
