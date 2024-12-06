from .imports import *


class CartViewSet(ModelViewSet):
    http_method_names = ['get', 'delete', 'options', 'head']
    lookup_field = 'id'
    serializer_class = CartSerializer
    pagination_class = StandardResultSetPagination
    lookup_value_regex = '[0-9A-Za-z]{8}\-?[0-9A-Za-z]{4}\-?[0-9A-Za-z]{4}\-?[0-9A-Za-z]{4}\-?[0-9A-Za-z]{12}'

    def is_admin_or_manager(self):
        user = self.request.user
        if user.is_authenticated and (user.is_superuser or user.groups.filter(name='Order Manager').exists()):
            return True
        
    def get_serializer_class(self):
        return ManagerCartSerializer if self.is_admin_or_manager() else CartSerializer
    
    def get_queryset(self):
        user = self.request.user
        session_key = self.request.session.session_key
        queryset =  Cart.objects.prefetch_related(
                        Prefetch('items', queryset=CartItem.objects.select_related('product'))
                    )

        if self.is_admin_or_manager():
            return queryset.all().order_by('-created_at')
        
        if user.is_authenticated:
            carts = queryset.filter(user=user)
        else:
            carts = queryset.filter(session_key=session_key)

        if not carts.exists():
            raise NotFound()
        return carts
    
    def paginate_queryset(self, queryset):
        if self.is_admin_or_manager():
            return super().paginate_queryset(queryset)
    
    def list(self, request, *args, **kwargs):
        user = request.user
        session_key = request.session.session_key

        if user.is_authenticated:
            # over queriyng with every request
            has_anon_cart = Cart.objects.filter(session_key=session_key).first()
            has_auth_cart = Cart.objects.filter(user=user).first()

            if has_anon_cart and not has_auth_cart:
                # Trigger the Celery task to change anon cart to auth cart asynchronously
                change_anon_cart_to_auth_cart.delay(user.id, session_key)
                
            if has_anon_cart and has_auth_cart:
                # Trigger the Celery task to transit anon cart items to auth cart asynchronously
                transit_anon_cart_items_to_auth_cart_and_delete.delay(user.id, session_key)
        return super().list(request, *args, **kwargs)
    
    def get_throttles(self):
        return base_throttle.get_throttles(self.request)
    

class AddToCartView(ViewSet):
    http_method_names = ['post']

    @transaction.atomic()
    def create(self, request, product_slug:None):
        user = request.user

        if user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=user)
        else:
            cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)

        context = {
            'cart_id': cart.id,
            'product_slug': self.kwargs['product_slug'],
            'request': request,
        }

        item_creation_serializer = AddItemtoCartSerializer(data=request.data, context=context)
        item_creation_serializer.is_valid(raise_exception=True)

        try:
            created_item = item_creation_serializer.save()
        except IntegrityError:
            return Response('This product has already added to your cart', status=status.HTTP_400_BAD_REQUEST)

        cartitem_serializer = CartItemSerializer(created_item, context={'request': request})

        return Response(cartitem_serializer.data, status=status.HTTP_201_CREATED)


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete', 'options', 'head']
    lookup_field = 'pk'

    def is_admin_or_manager(self):
        user = self.request.user
        if user.is_authenticated and (user.is_superuser or user.groups.filter(name='Order Manager').exists()):
            return True

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ManagerAddItemtoCartSerializer 
        
        return ManagerCartItemSerializer if self.is_admin_or_manager() else CartItemSerializer
    
    def get_serializer_context(self):
        context = {
            'cart_id': self.kwargs['cart_id'],
            'request': self.request
        }
        return context

    def get_queryset(self):
        request = self.request
        cart_id = self.kwargs['cart_id']
        queryset = CartItem.objects.select_related('cart', 'product').filter(
            cart__id=cart_id
            ).order_by('-quantity')
        
        if self.is_admin_or_manager():
            return queryset
        if request.user.is_authenticated:
            cartitems = queryset.filter(cart__user=request.user)
        else:
            cartitems = queryset.filter(cart__session_key=request.session.session_key)
        
        if not cartitems.exists():
            raise NotFound()
        return cartitems
    
    def create(self, request, *args, **kwargs):
        # add item to cart with AddItemtoCartSerializer
        context = {'cart' : Cart.objects.get(id=self.kwargs['cart_id']), 'request' : request}
        item_creation_serializers = ManagerAddItemtoCartSerializer(data=request.data, context=context)
        item_creation_serializers.is_valid(raise_exception=True)

        # Get request and observing the items is with CartItemSerializer
        created_item = item_creation_serializers.save()
        get_request_serializer = CartItemSerializer(created_item, context={'request': request})
        return Response(get_request_serializer.data, status=status.HTTP_201_CREATED)
    
    def paginate_queryset(self, queryset):
        if self.is_admin_or_manager:
            return super().paginate_queryset(queryset)

    def get_permissions(self):
        if self.request.method in ['POST']:
            return [IsOrderManager()]
        return [AllowAny()]
    
    @transaction.atomic
    def destroy(self, request, pk, cart_id):
        cartitem = get_object_or_404(CartItem.objects.select_related('cart'), pk=pk)
        cart = cartitem.cart

        cartitem.delete()

        if cart.items.count() == 0:
            cart.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def get_throttles(self):
        return base_throttle.get_throttles(self.request)