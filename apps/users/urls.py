from django.urls import path

from apps.users.views import (
    user_detail_view,
    user_redirect_view,
    user_update_view,
    CreateTokenView,
    CreateUserView,
    ManageUserView
)

app_name = "users"
urlpatterns = [
    # path("~redirect/", view=user_redirect_view, name="redirect"),
    # path("~update/", view=user_update_view, name="update"),
    # path("<str:id>/", view=user_detail_view, name="detail"),

    path('create/', CreateUserView.as_view(), name='create'),
    path('token/', CreateTokenView.as_view(), name='token'),
    path('me/', ManageUserView.as_view(), name='me'),
]
