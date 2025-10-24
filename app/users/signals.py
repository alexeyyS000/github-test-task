from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from users.utils.sync_repo import sync_user_repos_to_db


@receiver(user_logged_in)
def on_user_logged_in(sender, user, request, **kwargs):
    from allauth.socialaccount.models import SocialAccount

    if SocialAccount.objects.filter(user=user, provider="github").exists():
        sync_user_repos_to_db(user)
