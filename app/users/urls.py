from django.urls import include
from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.GitHubLoginView.as_view(), name="github_login"),
    path("", include("allauth.urls")),
    path("github/repos/", views.GitHubReposView.as_view(), name="github_repos"),
]
