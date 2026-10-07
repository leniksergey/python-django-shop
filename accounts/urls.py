from django.urls import path
from . import views

urlpatterns = [
    path("sign-in", views.sign_in),
    path("sign-up", views.sign_up),
    path("sign-out", views.sign_out),
    path("profile", views.profile_view),
    path("profile/avatar", views.avatar_upload_view),
    path("profile/password", views.change_password_view),
]
