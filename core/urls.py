from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from champions.views import signup_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("champions.urls", "champions"), namespace="champions")),
    path("worldcup/", include(("worldcup.urls", "worldcup"), namespace="worldcup")),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("accounts/signup/", signup_view, name="signup"),
]
