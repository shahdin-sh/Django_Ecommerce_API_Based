from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from store.models import Cart
from .thread_local import get_current_request


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def change_cart_type_from_anon_to_auth_after_user_creation(sender, instance, created, **kwargs):
    if created:
        request = get_current_request()
        
        if request:
            session_key = request.session.session_key
            
            try:
                cart = Cart.objects.get(session_key=session_key)

                # set the session key to none and modify based on the current user
                with transaction.atomic():
                    cart.session_key = None
                    cart.user = instance
                    cart.save()

            except Cart.DoesNotExist:
                return None
    
    # TODO: 4 scenarios are possible within the cart and user status
    # sc1) user is auth user and create a cart (the cart will created by his name in DB at the first place).
    # sc2) user is anon user and will create a cart after that he will sign up and the user cart status from 
    # session key will switch to auth user.
    # sc3) user has signed up before so he creates a cart as an anon user and login after that, then the above scenario
    # is gonna happened again(log in or sign up).
    # sc4) user has cart and item in his auth cart so he will create another cart as an anon user then after user 
    # login again his anon cart will be deleted and its items will merged with his current auth cart items.