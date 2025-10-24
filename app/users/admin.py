from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import GitHubRepo

User = get_user_model()


@admin.register(GitHubRepo)
class GitHubRepoAdmin(admin.ModelAdmin):
    list_display = ("name", "full_name", "user", "stargazers_count", "forks_count", "language", "private")
    list_filter = ("private", "language")
    search_fields = ("name", "full_name", "user__username")
    ordering = ("-stargazers_count",)
