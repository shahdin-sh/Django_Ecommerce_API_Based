from django.db import IntegrityError
from django.utils.timezone import now

from celery import shared_task

from .models import Order, Product

@shared_task(bind=True)
def approve_order_status_after_successful_payment(self, order_id):
    try:
        order_obj = Order.objects.get(id=order_id)

        # this if statement ensures that order wont save multiple times due to some unexcepted error
        if order_obj.status != 'paid':
            order_obj.status = 'paid'
            order_obj.save()

        return f"order {order_id} for {order_obj.customer.user.username} approved successfully."
    
    except Exception as exc:
        self.retry(exc=exc, countdown=5, max_retries=3)  # Retry mechanism for Celery


@shared_task()
def update_inventory(product_id:int, quantity:int, reduce: bool):
    try:
        product = Product.objects.get(id=product_id)

        if reduce:
            product.inventory -= quantity
            keyword = 'reduced'
        else:
            product.inventory += quantity
            keyword = 'added'
        
        product.save()

        return f"Inventory {keyword} for {product.name} | Current Inventory: {product.inventory} | Amount: {quantity}"
    
    except IntegrityError as e:
        error_msg = f"Warning: Failed to update inventory for product {product.name} and the amount of {quantity} | {str(e)}"
        return error_msg
    
    except Exception as e:
        return f"Warning: Failed to update inventory due to {e}"

@shared_task()
def remove_expired_orders():
    expired_orders = Order.objects.filter(expires_at__lt=now()).exclude(status__in=['paid'])
    list_of_expired_orders = list(expired_orders)
    expired_orders.delete()

    return f'Deleted {list_of_expired_orders}'