from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.db.models import ProtectedError
from django.conf import settings

from .models import Customer, OrderItem, Order


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_instance_for_newly_signed_up_users(sender, instance, created, **kwargs):
    if created or not hasattr(instance, 'customer'):
        Customer.objects.create(user=instance)
    elif instance.is_staff or instance.is_superuser:
        if hasattr(instance, 'customer'):
            try:
                instance.customer.delete()
            except ProtectedError:
                [order.delete() for order in Order.objects.filter(customer__user=instance)]
