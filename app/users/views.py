from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialApp
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import Http404, HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from users.tasks import sync_repos as sync_repos_task
from http import HTTPStatus
from django_ratelimit.decorators import ratelimit

from .models import UserGitHubRepo

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

        links_qs = (
            UserGitHubRepo.objects.select_related('repo')
            .filter(user=self.request.user)
            .order_by('-repo__stargazers_count')
        )

        repos_list = []
        for link in links_qs:
            r = link.repo
            repos_list.append({
                'full_name': r.full_name,
                'html_url': r.html_url,
                'description': r.description,
                'stargazers_count': r.stargazers_count,
                'forks_count': r.forks_count,
                'language': r.language,
                'disabled': link.disabled,
                'private': r.private,
            })

        page_number_raw = self.request.GET.get("page_num", 1)
        page_size_raw = self.request.GET.get("page_size", 10)
        try:
            page_number = int(page_number_raw)
            page_size = int(page_size_raw)
            if page_number < 1 or page_size < 1:
                raise ValueError()
        except (ValueError, TypeError):
            raise Http404("Not found")

        paginator = Paginator(repos_list, page_size)
        try:
            page_obj = paginator.page(page_number)
        except (EmptyPage, PageNotAnInteger):
            raise Http404("Not found")

        context["page_number"] = page_number
        context["repos"] = page_obj
        return context

@login_required
@require_POST
@ratelimit(key='user', rate='1/m', block=True)
def trigger_sync_repos(request):
    sync_repos_task.delay(request.user.id)
    return HttpResponse(status=HTTPStatus.ACCEPTED)


#TODO sertbot queries db and all