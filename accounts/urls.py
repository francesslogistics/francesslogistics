from django.urls import path

from .views import (
    accounts_detail_view,
    accounts_list_view,
    change_password_view,
    login_view,
    logout_view,
    me_view,
    my_login_activity_view,
    ping,
    register_view,
)

urlpatterns = [
    path("ping/", ping, name="accounts-ping"),
    path("login/", login_view, name="accounts-login"),
    path("logout/", logout_view, name="accounts-logout"),
    path("register/", register_view, name="accounts-register"),
    path("me/", me_view, name="accounts-me"),
    path("me/password/", change_password_view, name="accounts-change-password"),
    path("me/activity/", my_login_activity_view, name="accounts-my-activity"),
    path("users/", accounts_list_view, name="accounts-list"),
    path("users/<int:user_id>/", accounts_detail_view, name="accounts-detail"),
]
