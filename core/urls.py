from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from worldcup.views import signup_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("worldcup.urls")),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="dashboard"), name="logout"),
    path("accounts/signup/", signup_view, name="signup"),
]