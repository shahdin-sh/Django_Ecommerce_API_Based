import jwt 
from rest_framework.authentication import get_authorization_header
from django.contrib.auth import get_user_model
from django.utils.functional import SimpleLazyObject
from django.db import transaction
from store.models import Cart,CartItem

User = get_user_model()

def get_user_from_auth_header(request):
    # Retrieve user from JWT token in the Authorization header, this function returns header as byte string

    # JWT processed only in view layer not in Middleware layer so here the request.user and user might not be the same
    # this function only works in Middleware layer so it accessed the user from jwt not from the request.user
    auth_header = get_authorization_header(request).decode('utf-8').split()

    if auth_header and auth_header[0] == 'JWT':
        try:
            token = auth_header[1]
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get('user_id')
            user = User.objects.get(id=user_id)
            return user
        except jwt.InvalidTokenError:
            pass


class CartTransitionMiddleware:
    def __init__(self, get_response):
        # response is a callable that Django passes to each middleware.
        # It represents the next stage in the processing chain for each request (usually the next middleware or the view itself).

        self.get_response = get_response
    
    def __call__(self, request):
        # Behavior of SimpleLazyObject:
        # - Initial Access: When request.user is accessed for the first time,
        #   SimpleLazyObject evaluates the lambda function (e.g., get_user_from_jwt(request))
        #   to retrieve the user.
        #
        # - Caching the Result:
        #   - If the function returns a valid user object (not None), this user object is cached.
        #   - Subsequent accesses to request.user return the cached user object without re-evaluating the function.
        #
        # - Return None Handling:
        #   - If the function returns None (e.g., due to an invalid token), request.user is set to None
        #     and remains None for all subsequent accesses.
        #   - In this case, the function is only called once, and None is cached until valid user returns.

        user  = SimpleLazyObject(lambda: get_user_from_auth_header(request))

        # implement cart transition logic
        if user and user.is_authenticated:
            session_key = request.session.session_key
            session_cart_exists = Cart.objects.filter(session_key=session_key).exists()
            user_cart_exists = Cart.objects.filter(user=user).exists()

            if session_cart_exists and not user_cart_exists:
                cart = Cart.objects.get(session_key=session_key)
                
                with transaction.atomic():
                    cart.session_key = None
                    cart.user = user
                    cart.save()

            if session_cart_exists and user_cart_exists:
                session_cart = Cart.objects.get(session_key=session_key)
                user_cart = Cart.objects.get(user=user)

                with transaction.atomic():
                    cartitems_to_create = []
                    for item in session_cart.items.all():
                        if not CartItem.objects.filter(cart=user_cart, product=item.product).exists():
                            cartitems_to_create.append( 
                                CartItem(
                                cart = user_cart,
                                product = item.product,
                                quantity = item.quantity,
                                )
                            )
                    # delete session_cart first to avoid any product inventory issue 
                    session_cart.delete()
                    if cartitems_to_create:
                        CartItem.objects.bulk_create(cartitems_to_create)

        return self.get_response(request)