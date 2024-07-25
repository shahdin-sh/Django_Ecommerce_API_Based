import requests, json
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.exceptions import ValidationError

from .serializers import *
from .filters import ProductFilter, OrderFilter
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
        return base_throttle.get_throttles(request=self.request, throttle_scope=self.throttle_scope, group_name='Product Manager')
    

# Category View
class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    queryset = Category.objects.all().annotate(
            # with annotate method, products_count is known as a Category field when this view is called.
            products_count = Count('products')
        ).prefetch_related('products').order_by('-products_count')
    filter_backend = [SearchFilter, DjangoFilterBackend]
    search_fields = ['title']
    filterset_fields  = ['title']
    pagination_class = StandardResultSetPagination
    permission_classes = [IsProductManager]

    def destroy(self, request, slug):
        category = get_object_or_404(Category.objects.all().annotate(products_count = Count('products')), slug=slug)
        if category.products.count() > 0:
            return Response(
                f'{category.title} referenced through protected foreign key:{[product for product in category.products.all()]}', 
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        
        category.delete()
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)
    
    def get_throttles(self):
        self.throttle_scope = 'category'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Product Manager')
    

# Comment View
class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = ['datetime_created', 'name']
    pagination_class = StandardResultSetPagination
    permission_classes = [IsContentManager]

    def get_queryset(self):
        return Comment.objects.select_related('product').filter(
            product__slug=self.kwargs['product_slug']).all()
    
    def get_serializer_context(self):
        context = {
            'product' : Product.objects.get(slug=self.kwargs['product_slug'])
        }
        return context
    
    def get_throttles(self):
        self.throttle_scope = 'comment'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Content Manager')


# Cart View
class CartViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'delete']
    serializer_class = CartSerializer
    queryset = Cart.objects.prefetch_related(
        Prefetch('items', queryset=CartItem.objects.select_related('product'))
        ).all()
    lookup_field = 'id'
    pagination_class = StandardResultSetPagination
    permission_classes = [IsAuthenticated]
    lookup_value_regex = '[0-9A-Za-z]{8}\-?[0-9A-Za-z]{4}\-?[0-9A-Za-z]{4}\-?[0-9A-Za-z]{4}\-?[0-9A-Za-z]{12}'

    def get_throttles(self):
        return base_throttle.get_throttles(self.request)


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddItemtoCartSerializer
        
        return CartItemSerializer

    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        return CartItem.objects.select_related('cart', 'product').filter(cart__id=cart_id).all()
    

    def create(self, request, *args, **kwargs):
        # add item to cart with AddItemtoCartSerializer
        context = {'cart' : Cart.objects.get(id=self.kwargs['cart_id']), 'request' : request}
        item_creation_serializers = AddItemtoCartSerializer(data=request.data, context=context)
        item_creation_serializers.is_valid(raise_exception=True)

        # Get request and observing the items is with CartItemSerializer
        created_item = item_creation_serializers.save()
        get_request_serializer = CartItemSerializer(created_item, context={'request': request})
        return Response(get_request_serializer.data, status=status.HTTP_201_CREATED)
    
    def get_throttles(self):
        return base_throttle.get_throttles(self.request)
    

# Customer & Address View
class CustomerViewSet(ModelViewSet):
    # each new user has customer model so post method is not allowed
    http_method_names = ['get', 'put']
    serializer_class = CustomerSerializer
    queryset = Customer.objects.select_related('user').prefetch_related('address').all()
    permission_classes = [IsCustomerManager]

    @action(detail=False, methods=['GET', 'PUT', 'DELETE'], permission_classes=[IsAuthenticated])
    def me(self, request):
        customer = Customer.objects.select_related('user').get(user=request.user)
        if request.method == 'GET':
            # no need of get_object_or_404 because of customer creation signal for newly signed up users
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, request.data)
            serializer.is_valid(raise_exception=True)

            serializer.save()
            return Response(status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['GET'])
    def send_private_email(self, request, pk):
        target_customer = Customer.objects.get(pk=pk)
        return Response(f'send private email to {target_customer.user.username} by {request.user.username}')

    def get_throttles(self):
      self.throttle_scope = 'customer'
      return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Customer Manager')


class AddressViewSet(ModelViewSet):
    def get_queryset(self):
        queryset = Address.objects.select_related('customer').order_by('customer__user__username')
        # including admins and customer managers
        if self.request.user.is_staff:
            return queryset.all()
        # including authenticated users
        user_queryset = queryset.filter(customer__user=self.request.user)
        if user_queryset.exists():
            return user_queryset
        return user_queryset.none()

    def get_serializer_class(self):
        if self.request.user.is_superuser or self.request.user.groups.filter(name='Customer Manager').exists():
            if self.request.method == 'POST':
                return ManagersAddAddressSerializer
            return ManagerAddressSerializer
        
        if self.request.method == 'POST':
            return AddAddressSerializer
        return AddressSerializer
        
    def get_permissions(self):
        if self.request.method in ['DELETE']:
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

    def get_queryset(self):
        queryset = Order.objects.prefetch_related(
            Prefetch('items', OrderItem.objects.select_related('product')),
        ).select_related('customer').order_by('-datetime_created')
        
        user = self.request.user
        # Order Managers and admins included
        if user.is_staff:
            return queryset.all()
            
        return queryset.filter(customer__user_id=user.id)

    def get_serializer_class(self):
        # get serializer class based on http method
        if self.request.method == 'POST':
            return OrderCreationSerializer
        
        # get serializer class based on user authentication 
        if self.request.user.is_staff:
            return AdminOrderSerializer
        return OrderSerializer
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        if queryset.count() == 0 and not request.user.is_staff:
            return Response('You have no orders', status=status.HTTP_200_OK)
        
        # apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)    
    
    def create(self, request, *args, **kwargs):
        # create and save  the instance from OrderCreationSerializer
        order_creation_serializer = OrderCreationSerializer(data=request.data, context={'request': self.request})
        order_creation_serializer.is_valid(raise_exception=True)
        created_order = order_creation_serializer.save()

        # showing data in OrderSerializer
        serializer = OrderSerializer(created_order)
        return Response(serializer.data , status=status.HTTP_201_CREATED)
    
    def get_permissions(self):
        if self.request.method in ['DELETE', 'PATCH', 'PUT']:
            return [IsOrderManager()]
        return [IsAuthenticated()]
    
    def get_throttles(self):
      self.throttle_scope = 'order'
      return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Order Manager')

    
class PaymentProcess(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        authority = request.GET.get('Authority')
        payment_request_status = request.GET.get('Status')

        if payment_request_status == 'OK':
            # payment verification request to zarinpal 
            verify_request_url = "https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json"
           
            request_header = {
                'accept': 'application/json',
                'content-type': 'application/json' 
            }

            payment_data = request.session['payment_data']

            data_body = {
                'MerchantID': payment_data['merchant_id'],
                'Amount': payment_data['amount'],
                'Authority': authority
            }

            response = requests.post(url=verify_request_url, data=json.dumps(data_body), headers=request_header)
        
            try: 
                data = response.json()
            except json.JSONDecodeError as e:
                print(response.json())
                return Response({"error": "Invalid JSON response from the payment gateway."}, status=status.HTTP_400_BAD_REQUEST)
            
            if data['Status'] == 100:

                # set the order status to paid and save it in DB
                order_obj = Order.objects.select_related('customer').prefetch_related('items').get(id=payment_data['order_id'])
                order_obj.status = 'paid'
                order_obj.save()

                return Response(f"Transaction success. | RefID: {data['RefID']}.", status=status.HTTP_200_OK)
            
            elif data['Status'] == 101:
                return Response(f"Transaction is submitted before. | RefID: {data['RefID']}", status=status.HTTP_200_OK)
            
            else:
                return Response(f"Transaction failed. | Status: {data['Status']}", status=status.HTTP_400_BAD_REQUEST)
                        
        elif payment_request_status == 'NOK':
            return Response('Transaction failed or canceled by user.', status=status.HTTP_400_BAD_REQUEST)
        
        return Response('Enter your OrderId to initiate the payment process.', status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = PaymentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        order_id = request.data['order_id']
        order_obj = Order.objects.select_related('customer').prefetch_related('items').get(id=order_id)
        
        # payment data request to zarinpal
        zarinpal_request_url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json'

        request_header = {
            'accept': 'application/json',
            'content-type': 'application/json'
        }

        data_body = {
            'MerchantID': '1344b5d5-0048-11e8-94db-005056a205be',
            'Amount': order_obj.total_items_price,
            'Description': f'Transaction for {order_obj.customer} customer | OrderID: {order_obj.id}',
            'CallbackURL': 'http://127.0.0.1:8000/store/payment'
        }

        response = requests.post(url=zarinpal_request_url, data=json.dumps(data_body), headers=request_header)

        try: 
            data = response.json()
        except json.JSONDecodeError as e:
            return Response({"error": "Invalid JSON response from the payment gateway."}, status=status.HTTP_400_BAD_REQUEST)

        authority = data['Authority']
    
        if data['Status'] == 100 and 'errors' not in data and authority != '':
            # delete the session about previous transaction
            if request.session.get('payment_data'):
                del request.session['payment_data']

            # if post request to zarinpal was successful store payment data in session in order to have them in GET request
            request.session['payment_data'] = {
                'merchant_id' : data_body['MerchantID'],
                'amount': data_body['Amount'],
                'order_id': order_id
            }

            payment_url = 'https://sandbox.zarinpal.com/pg/StartPay/{authority}'.format(authority=authority)
            return Response(f'paymant_url: {payment_url}', status=status.HTTP_200_OK)
        else:
            return Response(f"failed because of errors : {data.get('errors')}", status=status.HTTP_400_BAD_REQUEST)
    
    def get_throttles(self):
        self.throttle_scope = 'payment'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope)