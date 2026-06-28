from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import ProductivityProfile, User


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    """Every user gets exactly one ProductivityProfile."""
    if created:
        ProductivityProfile.objects.get_or_create(user=instance)
