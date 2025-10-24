from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.GitHubLoginView.as_view(), name='github_login'),
    path('', include('allauth.urls')),
    path('github/repos/', views.GitHubReposView.as_view(), name='github_repos'),
]
