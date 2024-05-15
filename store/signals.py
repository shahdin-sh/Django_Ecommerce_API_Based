from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from .models import Customer

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_instance_for_newly_signed_up_users(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)