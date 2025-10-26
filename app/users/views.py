from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialApp
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from .models import GitHubRepo


class GitHubLoginView(TemplateView):
    template_name = "login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["github_app"] = SocialApp.objects.filter(provider="github").first()
        return context


class GitHubReposView(LoginRequiredMixin, TemplateView):
    template_name = "github_repos.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            account = SocialAccount.objects.get(user=self.request.user, provider="github")
            context["avatar_url"] = account.extra_data.get("avatar_url")
        except SocialAccount.DoesNotExist:
            context["error"] = "GitHub account not found."
            return context

        repos = GitHubRepo.objects.filter(user=self.request.user).order_by("-stargazers_count")
        context["repos"] = repos

        return context
