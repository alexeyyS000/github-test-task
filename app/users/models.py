from django.conf import settings
from django.db import models


class GitHubRepo(models.Model):
    github_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=300)
    full_name = models.CharField(max_length=400)
    html_url = models.URLField(max_length=1000)
    description = models.TextField(blank=True, null=True)
    stargazers_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    language = models.CharField(max_length=100, blank=True, null=True)
    private = models.BooleanField(default=False)

    class Meta:
        ordering = ["-stargazers_count"]

    def __str__(self):
        return self.full_name


class UserGitHubRepo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    repo = models.ForeignKey(GitHubRepo, on_delete=models.CASCADE)
    disabled = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "repo")
