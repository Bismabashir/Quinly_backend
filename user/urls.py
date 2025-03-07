from django.urls import path
from .views import register_user, login_user, get_user_profile, get_all_users, forgot_password, reset_password

urlpatterns = [
    path("register/", register_user, name="register"),
    path("login/", login_user, name="login"),
    path("profile/", get_user_profile, name="user-profile"),
    path("all-users/", get_all_users, name="get-all-users"),
    path("forgot-password/", forgot_password, name="forgot-password"),
    path("reset-password/", reset_password, name="reset-password"),
]
