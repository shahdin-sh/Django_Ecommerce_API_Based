import requests, json
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from django.db import IntegrityError
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from .serializers import *
from .filters import ProductFilter, OrderFilter, CustomerWithOutAddress
from .models import Product, Category, Comment, Cart, CartItem, Customer, Address, Order, OrderItem
from .paginations import StandardResultSetPagination, LargeResultSetPagination
from .permissions import IsAdminOrReadOnly, IsProductManager, IsContentManager, IsCustomerManager, IsAdmin, IsOrderManager 
from .throttle import AdminUserThrottle, BaseThrottleView


# Determines the appropriate throttle class based on throttle_scopes and four types of user 
# inlucding: superusers, managers, anonymous users and authenticated users.
base_throttle = BaseThrottleView()

# Product view
class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    queryset = Product.objects.prefetch_related('comments').select_related('category').annotate(
        comments_count=Count('comments')
        ).all().order_by('-id')
    filter_backends = [SearchFilter, OrderingFilter , DjangoFilterBackend]
    filterset_class = ProductFilter
    ordering_fields = ['name', 'inventory', 'unit_price']
    search_fields = ['name', 'category__title']
    pagination_class = LargeResultSetPagination
    permission_classes = [IsProductManager]

    CACHE_KEY_PREFIX = "product_list"

    @method_decorator(cache_page(60 * 15, key_prefix=CACHE_KEY_PREFIX))
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)

        if page:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)

            return paginated_response
    
    def retrieve(self, request, *args, **kwargs):
        # custom caching to get the product slug dynamically
        product_slug = kwargs.get('slug')
        product_cache = cache.get(product_slug)

        if product_cache:
            return Response(product_cache)
        
        try:
            product = self.get_queryset().get(slug=product_slug)
            serializer = ProductSerializer(product, context={'request': request})

            # cache serialized product before returning the response 
            cache.set(product_slug, serializer.data, 60 * 15)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            raise NotFound()

    def destroy(self, request, slug):
        product = get_object_or_404(Product.objects.select_related('category').all(), slug=slug)
        if product.order_items.count() > 0:
            return Response(
                f'{product.name} referenced through protected foreign key: {[orderitem for orderitem in product.order_items.all()]}', 
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        product.delete()
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    def get_throttles(self):
        self.throttle_scope = 'product'
        return base_throttle.get_throttles(
            request=self.request, 
            throttle_scope=self.throttle_scope, 
            group_name='Product Manager'
        )
    

# Category View
class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    queryset = Category.objects.all().annotate(
            # with annotate method, products_count is known as a Category field when this view is called.
            products_count = Count('products')
        ).prefetch_related('products').order_by('-products_count')
    filter_backends = [DjangoFilterBackend]
    filterset_fields  = ['title']
    pagination_class = StandardResultSetPagination
    permission_classes = [IsProductManager]

    def destroy(self, request, slug):
        category = get_object_or_404(Category.objects.all().annotate(products_count = Count('products')), slug=slug)
        if category.products.count() > 0:
            return Response(
                f'{category.title} referenced through protected foreign key: {[product for product in category.products.all()]}', 
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        
        category.delete()
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    def get_throttles(self):
        self.throttle_scope = 'category'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Product Manager')
    

# Comment View
class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    lookup_field = 'pk'
    filter_backends = [OrderingFilter]
    ordering_fields = ['datetime_created', 'name']
    pagination_class = StandardResultSetPagination
    permission_classes = [IsContentManager]

    def get_queryset(self):
        return Comment.objects.select_related('product').filter(
            product__slug=self.kwargs['product_slug'], status=Comment.COMMENT_STATUS_APPROVED).order_by('-datetime_created')
    
    def get_serializer_context(self):
        context = {
            'product' : Product.objects.get(slug=self.kwargs['product_slug'])
        }
        return context
    
    def get_throttles(self):
        self.throttle_scope = 'comment'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Content Manager')


# Wishlist Views
class WishlistViewSet(ModelViewSet):
    http_method_names = ['get', 'delete', 'options', 'head']
    lookup_field = 'id'
    serializer_class = WishlistSerializer
    pagination_class = StandardResultSetPagination

    def is_admin_or_manager(self):
        user = self.request.user
        if user.is_authenticated and (user.is_superuser or user.groups.filter(name='Product Manager').exists()):
            return True

    def get_queryset(self):
        user = self.request.user
        queryset = Wishlist.objects.select_related('user').prefetch_related('products')

        if self.is_admin_or_manager():
            return queryset.all().order_by('user__id')
        return queryset.filter(user=user)
    
    def paginate_queryset(self, queryset):
        if self.is_admin_or_manager():
            return super().paginate_queryset(queryset)
    
    def get_permissions(self):
        if self.request.method in ['DELETE']:
            return [IsProductManager()]
        return [IsAuthenticated()]


class AddToWishlist(ViewSet):
    http_method_names = ['post']

    @transaction.atomic()
    def create(self, request, product_slug:None):
        user_wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        product_slug = self.kwargs['product_slug']
        product = Product.objects.get(slug=product_slug)

        if product not in user_wishlist.products.all():
            user_wishlist.products.add(product)
            user_wishlist.save()
            return Response(
                f'Product {product.name} added to your wishlist successfully',
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                f'Product {product.name} has already added to your wishlist',
                status=status.HTTP_400_BAD_REQUEST
            )

class WishlistProductViewSet(ViewSet):
    http_method_names = ['get', 'delete', 'options', 'head']
    permission_classes = [IsAuthenticated]

    def get_queryset(self, wishlist_id):
        user = self.request.user
        
        try:
            queryset = Wishlist.objects.select_related('user').prefetch_related('products').get(
                id = wishlist_id,
                user = user
            )
            return queryset
        except Wishlist.DoesNotExist:
            raise NotFound()
    
    def list(self, request, wishlist_id=None):
        queryset = self.get_queryset(wishlist_id).products.all()
        serializer = WishlistProductSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, wishlist_id:None, pk):
        queryset = self.get_queryset(wishlist_id)

        try:
            product = queryset.products.get(id=pk)
            serializer = WishlistProductSerializer(product, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            raise NotFound()
    
    def destroy(self, request, wishlist_id:None, pk):
        queryset = self.get_queryset(wishlist_id)

        try:
            product = queryset.products.get(id=pk)

            queryset.products.remove(product)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            raise NotFound()

# Cart Views
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
        queryset =  Cart.objects.prefetch_related(
                        Prefetch('items', queryset=CartItem.objects.select_related('product'))
                    )

        if self.is_admin_or_manager():
            return queryset.all().order_by('-created_at')
        
        if user.is_authenticated:
            carts = queryset.filter(user=user)
        else:
            carts = queryset.filter(session_key=self.request.session.session_key)

        if not carts.exists():
            raise NotFound()
        return carts
    
    def paginate_queryset(self, queryset):
        if self.is_admin_or_manager():
            return super().paginate_queryset(queryset)
    
    def get_throttles(self):
        return base_throttle.get_throttles(self.request)
    

class AddToCartViewSet(ViewSet):
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
    

# Customer & Address View
class CustomerViewSet(ModelViewSet):
    # each new user has customer model so post method is not allowed
    http_method_names = ['get', 'put', 'head', 'options']
    serializer_class = ManagerCustomerSerializer
    queryset = Customer.objects.select_related('user').prefetch_related('address').order_by('id')
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_class = CustomerWithOutAddress
    search_fields = ['user__username']
    pagination_class = StandardResultSetPagination
    permission_classes = [IsCustomerManager]

    @action(detail=False, methods=['GET', 'PUT', 'HEAD', 'OPTIONS'], permission_classes=[IsAuthenticated])
    def me(self, request):
         # no need of get_object_or_404 because of customer creation signal for newly signed up users
        customer = Customer.objects.select_related('user').get(user=request.user)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        
        elif request.method == 'HEAD':
            return Response(status=status.HTTP_200_OK)
        
        elif request.method == 'OPTIONS':
            # Respond with allowed methods and other OPTIONS-related headers
            return Response(status=status.HTTP_200_OK)
         

    def get_throttles(self):
      self.throttle_scope = 'customer'
      return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Customer Manager')


class AddressViewSet(ModelViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['customer__user__username']
    pagination_class = None

    def is_manager(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Customer Manager').exists()

    def get_queryset(self):
        queryset = Address.objects.select_related('customer__user').order_by('pk')
       
        return queryset.all() if self.is_manager() else queryset.filter(customer__user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ManagersAddAddressSerializer if self.is_manager() else AddAddressSerializer
        elif self.request.method == 'PUT':
            return AddressSerializer
        else:
            return ManagerAddressSerializer if self.is_manager() else AddressSerializer
    
    def create(self, request, *args, **kwargs):
        if self.is_manager():
            creation_serializer = ManagersAddAddressSerializer
            serializer = ManagerAddressSerializer
        else:
            creation_serializer = AddAddressSerializer
            serializer = AddressSerializer
        
        creation_serializer = creation_serializer(data=request.data, context={'request': request})
        creation_serializer.is_valid(raise_exception=True)
        created_address = creation_serializer.save()

        serializer = serializer(created_address, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if self.is_manager():
            self.pagination_class = StandardResultSetPagination
            page = self.paginate_queryset(queryset)

            if page:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset ,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsCustomerManager()]
        return [IsAuthenticated()]
    
    def get_throttles(self):    
        self.throttle_scope = 'address'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Customer Manager')
    

# Order & OrderItem View
class OrderViewSet(ModelViewSet):
    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend]
    filterset_class = OrderFilter
    search_fields = ['customer__user__username']
    ordering_fields = ['datetime_created']
    pagination_class = StandardResultSetPagination

    def is_manager(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Order Manager').exists()

    def get_queryset(self):
        queryset = Order.objects.prefetch_related(
            Prefetch('items', OrderItem.objects.select_related('product')),
        ).select_related('customer__user', 'customer__address').order_by('-datetime_created')
        
        return queryset.all() if self.is_manager() else queryset.filter(customer__user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreationSerializer
        
        return ManagerOrderSerializer if self.is_manager() else OrderSerializer
     
    def create(self, request, *args, **kwargs):
        order_creation_serializer = OrderCreationSerializer(data=request.data, context={'request': self.request})
        order_creation_serializer.is_valid(raise_exception=True)
        created_order = order_creation_serializer.save()
        
        if self.is_manager():
          serializer = ManagerOrderSerializer(created_order)
        else:  
            serializer = OrderSerializer(created_order)

        return Response(serializer.data , status=status.HTTP_201_CREATED)
    
    # def destroy(self, request, *args, **kwargs):
    #     # showing the proper data when the instance get deleted
    #     pass

    def get_permissions(self):
        if self.request.method in ['DELETE', 'PATCH', 'PUT']:
            return [IsOrderManager()]
        return [IsAuthenticated()]
    
    def get_throttles(self):
      self.throttle_scope = 'order'
      return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Order Manager')

    
class PaymentProcess(APIView):
    http_method_names = ['get', 'post', 'head', 'options']
    permission_classes = [IsAuthenticated]

    def get(self, request):
        authority = request.GET.get('Authority')
        payment_request_status = request.GET.get('Status')

        if payment_request_status == 'OK':
            # payment verification request to zarinpal 
            verify_request_url = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
           
            request_header = {
                'accept': 'application/json',
                'content-type': 'application/json' 
            }

            payment_data = request.session['payment_data']

            data_body = {
                'merchant_id': payment_data['merchant_id'],
                'amount': payment_data['amount'],
                'authority': authority
            }

            response = requests.post(url=verify_request_url, data=json.dumps(data_body), headers=request_header)
        
            try: 
                data = response.json()
            except json.JSONDecodeError as e:
                print(response.json())
                return Response({"error": "Invalid JSON response from the payment gateway."}, status=status.HTTP_400_BAD_REQUEST)
            
            if data['data']['code'] == 100:

                # set the order status to paid and save it in DB
                order_obj = Order.objects.select_related('customer').prefetch_related('items').get(id=payment_data['order_id'])
                order_obj.status = 'paid'
                order_obj.save()

                return Response(f"Transaction success. | ref_id: {data['data']['ref_id']}.", status=status.HTTP_200_OK)
            
            elif data['data']['code'] == 101:
                return Response(f"Transaction is submitted before. | ref_id: {data['data']['ref_id']}", status=status.HTTP_200_OK)
            
            else:
                return Response(f"Transaction failed. | Status: {data['code']}", status=status.HTTP_400_BAD_REQUEST)
                        
        elif payment_request_status == 'NOK':
            return Response('Transaction failed or canceled by user.', status=status.HTTP_400_BAD_REQUEST)
        
        return Response('Enter your OrderId to initiate the payment process.', status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        order_id = request.data['order_id']
        order_obj = Order.objects.select_related('customer').prefetch_related('items').get(id=order_id)
        
        # payment data request to zarinpal
        zarinpal_request_url = 'https://sandbox.zarinpal.com/pg/v4/payment/request.json'

        request_header = {
            'accept': 'application/json',
            'content-type': 'application/json'
        }

        data_body = {
            'merchant_id': '1344b5d5-0048-11e8-94db-005056a205be',
            'amount': order_obj.total_items_price,
            'description': f'Transaction for {order_obj.customer} customer | OrderID: {order_obj.id}',
            'callback_url': 'http://0.0.0.0:8000/store/payment'
        }

        response = requests.post(url=zarinpal_request_url, data=json.dumps(data_body), headers=request_header)

        try: 
            data = response.json()
        except json.JSONDecodeError as e:
            return Response({"error": "Invalid JSON response from the payment gateway."}, status=status.HTTP_400_BAD_REQUEST)
        
        authority = data['data']['authority']

        if data['data']['code'] == 100 and data['data']['message'] == 'Success' and data['errors'] == []:
            # delete the session about previous transaction
            if request.session.get('payment_data'):
                del request.session['payment_data']

            # if post request to zarinpal was successful store payment data in session in order to have them in GET request
            request.session['payment_data'] = {
                'merchant_id' : data_body['merchant_id'],
                'amount': data_body['amount'],
                'order_id': order_id
            }

            payment_url = 'https://sandbox.zarinpal.com/pg/StartPay/{authority}'.format(authority=authority)
            return Response(f'paymant_url: {payment_url}', status=status.HTTP_200_OK)
        else:
            return Response(f"request failed, errors : {data.get('errors')}", status=status.HTTP_400_BAD_REQUEST)
    
    def get_throttles(self):
        self.throttle_scope = 'payment'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope)