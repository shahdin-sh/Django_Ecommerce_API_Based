from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import ProtectedError
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver
from django.utils.text import slugify

from config.utils import delete_decorative_cache

from .models import Customer, OrderItem, Order, Product



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


# Product cach handlers singals
@receiver(pre_save, sender=Product)
def delete_products_cache_before_saving_instance(sender, instance, **kwargs):
    detail_cache_key = instance.slug

    cache.delete(detail_cache_key)
    delete_decorative_cache('product_list')

    # this line make sure after caching is handled the slug is up to date 
    instance.slug = slugify(instance.name)


@receiver(pre_delete, sender=Product)
def delete_products_cache_before_instance_deletion(sender, instance, **kwargs):
    detail_cache_key = instance.slug

    cache.delete(detail_cache_key)
    delete_decorative_cache('product_list')
