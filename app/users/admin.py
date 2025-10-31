from django.contrib import admin
from .models import GitHubRepo, UserGitHubRepo

@admin.register(GitHubRepo)
class GitHubRepoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "github_id",
        "name",
        "full_name",
        "html_url",
        "language",
        "stargazers_count",
        "forks_count",
    )
    search_fields = ("name", "full_name", "github_id", "language")
    ordering = ("-stargazers_count",)
    readonly_fields = ("github_id",)

@admin.register(UserGitHubRepo)
class UserGitHubRepoAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "repo", "disabled")
    list_filter = ("disabled", "repo__language")
    search_fields = ("user__username", "repo__name", "repo__full_name")
    raw_id_fields = ("user", "repo")