from http import HTTPStatus
from unittest import mock

import pytest
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.test import Client
from django.urls import reverse
from users.models import GitHubRepo
from users.models import UserGitHubRepo

User = get_user_model()


@pytest.mark.django_db
class TestGitHubViews:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create(username="tester")
        self.user.set_unusable_password()
        self.user.save()
        site_pk = settings.SITE_ID
        Site.objects.get_or_create(pk=site_pk, defaults={"domain": "example.local", "name": "example.local"})

    def login(self):
        self.client.force_login(self.user)

    def test_login_view_includes_github_app_in_context(self):
        app = SocialApp.objects.create(provider="github", name="GH", client_id="x", secret="s")
        site = Site.objects.get(pk=settings.SITE_ID)
        app.sites.add(site)
        url = reverse("login_github")
        resp = self.client.get(url)
        assert resp.status_code == 200
        content = resp.content.decode()
        assert resp.context is not None
        assert resp.context.get("github_app") is not None
        assert resp.context.get("github_app").pk == app.pk
        try:
            provider_url = reverse("socialaccount_login", args=["github"])
        except Exception:
            provider_url = "/github/login/"
        assert provider_url in content or "provider_login_url" in content or "github/login" in content

    def test_github_repos_view_without_social_account_shows_error(self):
        self.login()
        url = reverse("github_repos")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.context is not None
        assert resp.context.get("error") == "GitHub account not found."

    def test_github_repos_view_pagination_invalid_raises_404(self):
        self.login()
        SocialAccount.objects.create(user=self.user, provider="github", uid="1", extra_data={})
        url = reverse("github_repos") + "?page_num=0&page_size=10"
        resp = self.client.get(url)
        assert resp.status_code == 404
        url = reverse("github_repos") + "?page_num=1&page_size=0"
        resp = self.client.get(url)
        assert resp.status_code == 404
        url = reverse("github_repos") + "?page_num=notint&page_size=10"
        resp = self.client.get(url)
        assert resp.status_code == 404

    def test_github_repos_view_empty_list_and_defaults(self):
        self.login()
        SocialAccount.objects.create(user=self.user, provider="github", uid="1", extra_data={"avatar_url": "http://x"})
        url = reverse("github_repos")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp.context is not None
        assert "repos" in resp.context
        page_obj = resp.context["repos"]
        assert hasattr(page_obj, "object_list")

    def test_github_repos_view_shows_repos_and_disabled_flag(self):
        self.login()
        SocialAccount.objects.create(user=self.user, provider="github", uid="1", extra_data={"avatar_url": "http://x"})
        r1 = GitHubRepo.objects.create(
            github_id=1,
            name="r1",
            full_name="u/r1",
            html_url="http://r1",
            stargazers_count=5,
            forks_count=1,
        )
        r2 = GitHubRepo.objects.create(
            github_id=2,
            name="r2",
            full_name="u/r2",
            html_url="http://r2",
            stargazers_count=10,
            forks_count=2,
            private=True,
        )
        UserGitHubRepo.objects.create(user=self.user, repo=r1, disabled=False)
        UserGitHubRepo.objects.create(user=self.user, repo=r2, disabled=True)
        url = reverse("github_repos")
        resp = self.client.get(url)
        assert resp.status_code == 200
        page = resp.context["repos"]
        objs = list(page.object_list)
        assert any(item["full_name"] == "u/r1" for item in objs)
        assert any(item["full_name"] == "u/r2" and item["disabled"] is True for item in objs)

    def test_trigger_sync_repos_starts_task_and_returns_json(self):
        self.login()
        SocialAccount.objects.create(user=self.user, provider="github", uid="1", extra_data={})
        fake_async = mock.MagicMock()
        fake_async.id = "task-123"

        with mock.patch("users.tasks.sync_repos", autospec=True) as patched_task:
            patched_task.delay.return_value = fake_async
            url = reverse("trigger_sync_repos")
            resp = self.client.post(url)
            assert resp.status_code == HTTPStatus.ACCEPTED

    def test_trigger_sync_repos_requires_login(self):
        url = reverse("trigger_sync_repos")
        resp = self.client.post(url)
        assert resp.status_code in (302, 401)
