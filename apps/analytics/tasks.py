from celery import shared_task

from .services import build_retrospective, update_profile_snapshot

@shared_task
def refresh_profile_snapshot(user_id):

    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None
    update_profile_snapshot(user)
    return user_id

@shared_task
def generate_retrospective_for_user(user_id):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None
    retro = build_retrospective(user)
    return retro.id

@shared_task
def generate_all_retrospectives():

    from django.contrib.auth import get_user_model

    User = get_user_model()
    count = 0
    for user in User.objects.filter(is_active=True):
        build_retrospective(user)
        update_profile_snapshot(user)
        count += 1
    return count
