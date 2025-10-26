from django.conf import settings
from django.db import models


class GitHubRepo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="github_repos")
    github_id = models.BigIntegerField()
    name = models.CharField(max_length=300)
    full_name = models.CharField(max_length=400)
    html_url = models.URLField(max_length=1000)
    description = models.TextField(blank=True, null=True)
    stargazers_count = models.IntegerField(default=0)
    forks_count = models.IntegerField(default=0)
    language = models.CharField(max_length=100, blank=True, null=True)
    private = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'github_id'], name='unique_user_github')
        ]
        ordering = ["-stargazers_count"]

    def __str__(self):
        return f"{self.full_name}"
