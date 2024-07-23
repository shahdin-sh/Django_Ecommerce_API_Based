from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction 
from django.conf import settings

from .models import Customer, OrderItem

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_customer_instance_for_newly_signed_up_users(sender, instance, created, **kwargs):
    if created:
        Customer.objects.create(user=instance)


@receiver(post_save, sender=OrderItem)
def reducing_order_products_inventory_after_order_creation(sender, instance, created, **kwargs):
    # first order creates then order items
    if created:
        # Reduce the product inventory based on the quantity of the OrderItem
        instance.product.inventory -= instance.quantity

        if instance.product.inventory == 0:
            instance.product.activation = False

        instance.product.save()


@receiver(post_delete, sender=OrderItem)
def restoring_order_products_inventory_after_order_deletion(instance, **kwargs):
    instance.product.inventory += instance.quantity

    if instance.product.activation == False:
        instance.product.activation = True

    instance.product.save()
