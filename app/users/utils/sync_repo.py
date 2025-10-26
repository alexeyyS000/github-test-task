import requests
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.models import SocialToken
from django.db import transaction
from users.models import GitHubRepo

def _get_github_token_for_user(user):
    try:
        account = SocialAccount.objects.get(user=user, provider="github")
    except SocialAccount.DoesNotExist:
        return None, None
    token_obj = SocialToken.objects.filter(account=account).first()
    token = token_obj.token if token_obj else None
    avatar_url = account.extra_data.get("avatar_url") if account.extra_data else None
    return token, avatar_url


def fetch_all_user_repos(token):
    if not token:
        return []
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Django-Allauth-App",
    }
    repos = []
    page = 1
    per_page = 100
    while True:
        params = {"per_page": per_page, "page": page, "sort": "updated"}
        r = requests.get("https://api.github.com/user/repos", headers=headers, params=params, timeout=10)
        if r.status_code != 200:
            break
        page_data = r.json()
        if not page_data:
            break
        repos.extend(page_data)
        if len(page_data) < per_page:
            break
        page += 1
    return repos

@transaction.atomic
def sync_user_repos_to_db(user):
    token, avatar_url = _get_github_token_for_user(user)
    if not token:
        return {"ok": False, "reason": "no_token"}
    api_repos = fetch_all_user_repos(token)
    if not api_repos:
        return {"ok": False, "reason": "no_api_repos"}
    api_map = {repo["id"]: repo for repo in api_repos}
    existing = GitHubRepo.objects.filter(user=user)
    existing_map = {r.github_id: r for r in existing}

    to_keep_ids = set()
    for github_id, data in api_map.items():
        to_keep_ids.add(github_id)
        obj = existing_map.get(github_id)
        updated_fields = {
            "name": data.get("name") or "",
            "full_name": data.get("full_name") or "",
            "html_url": data.get("html_url") or "",
            "description": data.get("description") or "",
            "stargazers_count": data.get("stargazers_count") or 0,
            "forks_count": data.get("forks_count") or 0,
            "language": data.get("language"),
            "private": data.get("private", False),
        }
        if obj:
            for k, v in updated_fields.items():
                setattr(obj, k, v)
            obj.save()
        else:
            GitHubRepo.objects.create(user=user, github_id=github_id, **updated_fields)
    GitHubRepo.objects.filter(user=user).exclude(github_id__in=to_keep_ids).delete()
    return {"ok": True, "count": len(api_map), "avatar_url": avatar_url}
