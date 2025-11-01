from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from .models import GitHubRepo
from .models import UserGitHubRepo


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
    list_filter = ("disabled",)
    search_fields = ("user__username", "repo__name", "repo__full_name")
    raw_id_fields = ("user", "repo")

    def get_queryset(self, request: HttpRequest) -> QuerySet[UserGitHubRepo]:
        qs = super().get_queryset(request)
        return qs.select_related("user", "repo")
