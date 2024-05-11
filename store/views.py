from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.mixins import RetrieveModelMixin, UpdateModelMixin, DestroyModelMixin, CreateModelMixin, ListModelMixin

from .paginations import StandardResultSetPagination, LargeResultSetPagination
from .filters import ProductFilter
from .models import Product, Category, Comment, Cart, CartItem
from .serializers import ProductSerializer, CategorySerializer, CommentSerializer, CartSerializer, CartItemSerializer, AddItemtoCartSerializer


# Product view
class ProductViewSet(ModelViewSet):

    serializer_class = ProductSerializer
    lookup_field = 'slug'

    queryset = Product.objects.prefetch_related('comments').select_related('category').annotate(
        comments_count=Count('comments')
        ).all()
    
    filter_backends = [SearchFilter, OrderingFilter , DjangoFilterBackend]
    filterset_class = ProductFilter
    ordering_fields = ['name', 'inventory', 'unit_price']
    search_fields = ['name', 'category__title']

    pagination_class = LargeResultSetPagination

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

    def get_queryset(self):
        return Comment.objects.select_related('product').filter(
            product__slug=self.kwargs['product_slug']).all()
    
    def get_serializer_context(self):
        context = {
            'product' : Product.objects.get(slug=self.kwargs['product_slug'])
        }
        return context 
    
    pagination_class = StandardResultSetPagination

    filter_backends = [OrderingFilter]
    ordering_fields = ['datetime_created', 'name']


# Cart View
class CartViewSet(ModelViewSet):
    serializer_class = CartSerializer
    queryset = Cart.objects.prefetch_related(
        Prefetch('items', queryset=CartItem.objects.select_related('product'))
        ).all()
    lookup_field = 'id'

    pagination_class = StandardResultSetPagination

    lookup_value_regex = '[0-9A-Za-z]{8}\-?[0-9A-Za-z]{4}\-?[0-9A-Za-z]{4}\-?[0-9A-Za-z]{4}\-?[0-9A-Za-z]{12}'


class CartItemViewSet(ModelViewSet):
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AddItemtoCartSerializer
        
        return CartItemSerializer


    def get_queryset(self):
        cart_id = self.kwargs['cart_id']
        return CartItem.objects.select_related('cart', 'product').filter(cart__id=cart_id).all()
    
    def get_serializer_context(self):
        context = {
            'cart' : Cart.objects.get(id=self.kwargs['cart_id']),
            'request' : self.request,
        }
        return context

