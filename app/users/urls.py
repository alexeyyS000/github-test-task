from django.urls import include
from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.GitHubLoginView.as_view(), name="login_github"),
    path("", include("allauth.urls")),
    path("github/repos/", views.GitHubReposView.as_view(), name="github_repos"),
    path("github/repos/trigger_sync/", views.trigger_sync_repos, name="trigger_sync_repos"),
]
