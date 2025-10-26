import pytest
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialApp
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.urls import NoReverseMatch
from django.urls import reverse
from users.models import GitHubRepo

User = get_user_model()


@pytest.fixture
def github_social_app(db):
    site = Site.objects.first() or Site.objects.create(domain="localhost", name="localhost")
    app = SocialApp.objects.create(
        provider="github",
        name="GitHub",
        client_id="test-client-id",
        secret="test-secret",
    )
    app.sites.add(site)
    return app


@pytest.fixture
def user(db):
    return User.objects.create_user(username="testuser", password="pass1234")


@pytest.fixture
def social_account(user, db):
    return SocialAccount.objects.create(
        user=user, provider="github", uid="12345", extra_data={"avatar_url": "https://avatar.url/avatar.png"}
    )


@pytest.mark.django_db
def test_github_login_button_present(client, github_social_app):
    url = reverse("github_login")
    response = client.get(url)
    assert response.status_code == 200
    content = response.content.decode()
    try:
        provider_url = reverse("socialaccount_login", args=["github"])
    except NoReverseMatch:
        pytest.skip("reverse('socialaccount_login', args=['github']) not found in this allauth version")

    assert provider_url in content or "/github/login/" in content


@pytest.mark.django_db
def test_github_repos_view_no_account(client, user):
    client.force_login(user)
    url = reverse("github_repos")
    response = client.get(url)
    assert response.status_code == 200
    assert "error" in response.context
    assert response.context["error"] == "GitHub account not found."
    assert list(response.context["repos"]) == []


@pytest.mark.django_db
def test_github_repos_view_no_repos(client, user, social_account):
    client.force_login(user)
    url = reverse("github_repos")
    response = client.get(url)
    assert response.status_code == 200
    assert "error" in response.context
    assert not response.context["repos"].exists()
    assert response.context["avatar_url"] == "https://avatar.url/avatar.png"


@pytest.mark.django_db
def test_github_repos_view_with_repos(client, user, social_account):
    repo1 = GitHubRepo.objects.create(
        user=user,
        github_id=1,
        name="Repo1",
        full_name="testuser/Repo1",
        html_url="https://github.com/testuser/Repo1",
        stargazers_count=5,
        forks_count=2,
        language="Python",
        private=False,
    )
    repo2 = GitHubRepo.objects.create(
        user=user,
        github_id=2,
        name="Repo2",
        full_name="testuser/Repo2",
        html_url="https://github.com/testuser/Repo2",
        stargazers_count=10,
        forks_count=1,
        language="Python",
        private=False,
    )
    client.force_login(user)
    url = reverse("github_repos")
    response = client.get(url)
    assert response.status_code == 200
    repos = response.context["repos"]
    assert list(repos) == [repo2, repo1]
    assert response.context["avatar_url"] == "https://avatar.url/avatar.png"
    assert "error" not in response.context or response.context["error"] is None


@pytest.mark.django_db
def test_github_repos_view_redirect_if_anonymous(client):
    url = reverse("github_repos")
    response = client.get(url)
    assert response.status_code == 302
    assert "/accounts/login/" in response.url
