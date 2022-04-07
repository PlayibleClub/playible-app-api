from django.urls import re_path, path, include

app_name = 'mlb'

urlpatterns = [
    re_path(r'^account/', include(('apps.api.mlb.account.urls', 'account'), namespace='account')),
    re_path(r'^fantasy/', include(('apps.api.mlb.fantasy.urls', 'fantasy'), namespace='fantasy')),
]
