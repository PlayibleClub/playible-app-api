from django.urls import re_path, include

app_name = 'api'
urlpatterns = [
    re_path(r'^mbl/', include('apps.api.mbl.urls', namespace='v1')),
]
