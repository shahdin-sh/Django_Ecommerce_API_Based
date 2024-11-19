from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils.timezone import now

from celery import shared_task

from .models import Order, Product, Cart, CartItem


CELERY_MESSAGES = {
    'successful': 'Successfull:',
    'warning': 'Warning:',
}

@shared_task(bind=True)
def approve_order_status_after_successful_payment(self, order_id):
    try:
        order_obj = Order.objects.get(id=order_id)

        # this if statement ensures that order wont save multiple times due to some unexcepted error
        if order_obj.status != 'paid':
            order_obj.status = 'paid'
            order_obj.save()

        return f"{CELERY_MESSAGES['successful']} order {order_id} for {order_obj.customer.user.username} approved."
    
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

        return f"{CELERY_MESSAGES['successful']} Inventory {keyword} for {product.name} | Current Inventory: {product.inventory} | Amount: {quantity}"
    
    except IntegrityError as e:
        error_msg = f"{CELERY_MESSAGES['warning']} Failed to update inventory for product {product.name} and the amount of {quantity} | {str(e)}"
        return error_msg
    
    except Exception as e:
        return f"{CELERY_MESSAGES['warning']} Failed to update inventory due to {e}"


@shared_task()
def remove_expired_orders():
    expired_orders = Order.objects.filter(expires_at__lt=now()).exclude(status__in=['paid'])
    list_of_expired_orders = list(expired_orders)
    expired_orders.delete()

    return f'Deleted {list_of_expired_orders}'


@shared_task()
@transaction.atomic()
def change_anon_cart_to_auth_cart(user_id: int, session_key): 
    try:
        user =  user = get_user_model().objects.get(id=user_id)
        anon_cart = Cart.objects.get(session_key=session_key)

        anon_cart.session_key = None
        anon_cart.user = user
        anon_cart.save()

        return f"{CELERY_MESSAGES['successful']} Change anon cart to {user.username}'s cart "
    except Exception as e:
        return f"{CELERY_MESSAGES['warning']} Change failed due to {e}"


@shared_task()
@transaction.atomic()
def transit_anon_cart_items_to_auth_cart_and_delete(user_id: int, session_key):
    try:
        # Celery can only work with simple, serializable data types. Passing an object like user is not possible directly, 
        # so you pass user.id (a simple integer), which Celery can handle.
        user = get_user_model().objects.get(id=user_id)

        anon_cart = Cart.objects.get(session_key=session_key)
        auth_cart = Cart.objects.get(user=user)

        cartiems_to_create = []
        cartiems_to_update = []
    
        # create a dictionary of auth_cart
        auth_cart_items_dict = {item.product.id: item for item in auth_cart.items.all()}

        for item in anon_cart.items.all():
            # check for mutal items, if there is any add the quantity to the auth cart item
            if item.product.id in auth_cart_items_dict:
                cartitem = auth_cart_items_dict[item.product.id]
                cartitem.quantity += item.quantity
                cartiems_to_update.append(cartitem)
            else:
                # if no mutal item, create anon_cart item in auth_cart
                cartitem = CartItem(
                    product=item.product,
                    quantity=item.quantity,
                    cart=auth_cart,
                )
                cartiems_to_create.append(cartitem)
        
        if cartiems_to_create:
            # If there are items to add, efficiently insert multiple new objects into the database in a single query
            CartItem.objects.bulk_create(cartiems_to_create)
        if cartiems_to_update:
            # If there are items to update, update specified fields (like 'quantity') 
            # of multiple existing objects in the database with a single query
            CartItem.objects.bulk_update(cartiems_to_update, ['quantity'])
        
        anon_cart.delete()

        return f"{CELERY_MESSAGES['successful']} Transit {cartiems_to_create} created and {cartiems_to_update} updated to {user.username}'s cart"
    except Exception as e:
        return f"{CELERY_MESSAGES['warning']} Tranistion failde due to {e}"