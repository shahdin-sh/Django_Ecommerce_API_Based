from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view, action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, CreateModelMixin, ListModelMixin
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from .paginations import StandardResultSetPagination, LargeResultSetPagination
from .filters import ProductFilter
from .models import Product, Category, Comment, Cart, CartItem, Customer, Address, Order, OrderItem
from .serializers import *
from .permissions import IsAdminOrReadOnly, IsProductManager, IsContentManager, IsCustomerManager, IsAdmin


# Product view
class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    queryset = Product.objects.prefetch_related('comments').select_related('category').annotate(
        comments_count=Count('comments')
        ).all().filter(inventory__gte=1)
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
    

# Category View
class CategoryViewSet(ModelViewSet):

    serializer_class = CategorySerializer
    lookup_field = 'slug'
    queryset = Category.objects.all().annotate(
            # with annotate method, products_count is known as a Category field when this view is called.
            products_count = Count('products')
        )
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


# Customer & Address View
class CustomerViewSet(ModelViewSet):
    # each new user has customer model so post method is not allowed
    http_method_names = ['get', 'put', 'delete']
    serializer_class = CustomerSerializer
    queryset = Customer.objects.select_related('user').prefetch_related('address').all()
    
    permission_classes = [IsCustomerManager]

    @action(detail=False, methods=['GET', 'PUT', 'DELETE'], permission_classes=[IsAuthenticated])
    def me(self, request):
        customer = Customer.objects.get(user=request.user)
        if request.method == 'GET':
            # no need of get_object_or_404 because of customer creation signal for newly signed up users
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, request.data)
            serializer.is_valid(raise_exception=True)

            serializer.save()
            return Response(status=status.HTTP_200_OK)
        elif request.method == 'DELETE':
            return Response('Each user should be a customer', status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @action(detail=True, methods=['GET'])
    def send_private_email(self, request, pk):
        target_customer = Customer.objects.get(pk=pk)
        return Response(f'send private email to {target_customer.user.username} by {request.user.username}')


class AdressViewSet(ModelViewSet):
    http_method_names = ['get', 'put']
    queryset = Address.objects.select_related('customer')
    permission_classes = [IsCustomerManager]

    def get_serializer_class(self):
        if self.action == 'list':
            return AddressListSerializer
        return AddressDetailSerializer

    def get_serializer_context(self):
        return {'request': self.request}
    
    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request):
        address = Address.objects.get(customer__user=request.user)
        if request.method == 'GET':
            serializer = AddressDetailSerializer(address)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = AddressDetailSerializer(address, request.data)
            serializer.is_valid(raise_exception=True)

            serializer.save()
            return Response(status=status.HTTP_200_OK)


# Order & OrderItem View
class OrderViewSet(ModelViewSet):
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['customer__user__username', 'status']
    ordering_fields = ['datetime_created', 'status']
    pagination_class = StandardResultSetPagination

    def get_queryset(self):
        queryset = Order.objects.prefetch_related(
            Prefetch('items', queryset=OrderItem.objects.select_related('product')),
            Prefetch('customer', queryset=Customer.objects.select_related('user').prefetch_related('address')),
        ).order_by('datetime_created')
        
        user = self.request.user
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
            return [IsAdmin()]
        return [IsAuthenticated()]