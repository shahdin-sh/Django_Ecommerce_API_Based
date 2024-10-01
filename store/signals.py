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
            
            
@receiver(post_save, sender=Order)
def deleting_order_if_order_status_is_canceled(sender, instance, created, **kwargs):
    if instance.status == Order.ORDER_STATUS_CANCELED:
        instance.delete()

        
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
def restoring_order_products_inventory_after_orderitem_deletion(instance, **kwargs):
    instance.product.inventory += instance.quantity

    if instance.product.activation == False:
        instance.product.activation = True

    instance.product.save()

