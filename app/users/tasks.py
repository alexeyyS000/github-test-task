import logging
import requests
from allauth.socialaccount.models import SocialAccount, SocialToken
from celery import shared_task
from django.contrib.auth import get_user_model
from django.db import transaction
from users.models import GitHubRepo, UserGitHubRepo
User = get_user_model()
logger = logging.getLogger(__name__)

@shared_task(max_retries=3)
def sync_repos(
    user_id: int
) :

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("sync_repos: user id %s does not exist", user_id)
        return {"ok": False, "reason": "user_not_found"}
    account = SocialAccount.objects.get(user=user, provider="github")
    token_obj = SocialToken.objects.filter(account=account).first()
    token = token_obj.token
    if not token:
        logger.warning("sync_repos: user id %s has no github token", user_id)
        return {"ok": False, "reason": "no_github_token"}

    api_repos = []
    params = {"per_page": 100, "page": 1, "sort": "created"}
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Django-Allauth-App",
    }
    r = requests.get("https://api.github.com/user/repos", headers=headers, params=params)
    page_data = r.json()
    api_repos.extend(page_data)


    api_map = {repo["id"]: repo for repo in api_repos}
    api_ids = set(api_map.keys())
    existing_repos = GitHubRepo.objects.filter(github_id__in=api_ids)
    existing_map = {r.github_id: r for r in existing_repos}
    kept_ids = set()
    to_create_repos = []
    to_update_repos = []
    to_create_user_links = []
    for github_id, data in api_map.items():
        kept_ids.add(github_id)
        repo_fields = {
            "name": data.get("name") or "",
            "full_name": data.get("full_name") or "",
            "html_url": data.get("html_url") or "",
            "description": data.get("description"),
            "stargazers_count": data.get("stargazers_count") or 0,
            "forks_count": data.get("forks_count") or 0,
            "language": data.get("language"),
            "private": data.get("private", False),
        }

        if github_id in existing_map:
            obj = existing_map[github_id]
            changed = False
            for k, v in repo_fields.items():
                if getattr(obj, k) != v:
                    setattr(obj, k, v)
                    changed = True
            if changed:
                to_update_repos.append(obj)

        else:
            to_create_repos.append(GitHubRepo(github_id=github_id, **repo_fields))
            to_create_user_links.append(UserGitHubRepo(user=user, repo=to_create_repos[-1]))


    with transaction.atomic():
        if to_create_repos:
            GitHubRepo.objects.bulk_create(to_create_repos)
        if to_update_repos:
            update_fields = ["name", "full_name", "html_url", "description", "stargazers_count", "forks_count", "language", "private"]
            GitHubRepo.objects.bulk_update(to_update_repos, update_fields)
        if kept_ids:
                UserGitHubRepo.objects.filter(user=user).exclude(repo__github_id__in=kept_ids).update(disabled=True)
                UserGitHubRepo.objects.bulk_create(to_create_user_links)


#TODO servbot  Certbot