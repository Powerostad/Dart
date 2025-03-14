from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from .tasks import optimize_profile_image

@receiver(post_save, sender=Profile)
def trigger_image_optimization(sender, instance, created, **kwargs):
    if instance.profile_picture:
        optimize_profile_image.delay(instance.id)