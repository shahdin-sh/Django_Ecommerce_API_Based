from django.db.models import Count, Prefetch
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend

from .models import Product, Category, Comment
from .serializers import ProductSerializer, CategorySerializer, CommentSerializer

# comply query optimization 

# product views
# ModelViewSet contains Creat, Retrieve, Update, Destroy and List model mixins
class ProductViewSet(ModelViewSet):

    def get_queryset(self):
        queryset = Product.objects.prefetch_related('comments').select_related('category').annotate(
        comments_count=Count('comments')
        ).order_by('-datetime_created').all()

        # url parameters
        category_slug_parameters = self.request.query_params.get('category_slug')
        lower_inventory_count_parameters  = self.request.query_params.get('lt')
        upper_inventory_count_parameters  = self.request.query_params.get('ut')

        if category_slug_parameters is not None:
            queryset = queryset.filter(category__slug=category_slug_parameters).all()
        if lower_inventory_count_parameters and upper_inventory_count_parameters is not None:
            queryset = queryset.filter(inventory__range=[upper_inventory_count_parameters , lower_inventory_count_parameters])
        
        return queryset
    
    serializer_class = ProductSerializer
    lookup_field = 'slug'

    def delete(self, request, slug):
        product = get_object_or_404(Product.objects.select_related('category').all(), slug=slug)
        if product.order_items.count() > 0:
            return Response(f'{product.name} referenced through protected foreign key: OrderItem', status=status.HTTP_405_METHOD_NOT_ALLOWED)

        product.delete()
        return Response(status=status.HTTP_404_NOT_FOUND)
    

# category views
class CategoryViewSet(ModelViewSet):

    queryset = Category.objects.all().annotate(
            # with annotate method, products_count is known as a Category field when this view is called.
            products_count = Count('products')
        )
    
    filter_backends = [DjangoFilterBackend]
    filterset_fields  = ['title']

    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def destroy(self, request, slug):
        category = get_object_or_404(Category.objects.all().annotate(products_count = Count('products')), slug=slug)
        if category.products.count() > 0:
            return Response(f'{category.title} referenced through protected foreign key: Product.', status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        category.delete()
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)


# comment views
class CommentViewSet(ModelViewSet):

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['datetime_created']

    serializer_class = CommentSerializer

    def get_queryset(self):
        return Comment.objects.select_related('product').filter(
            product__slug=self.kwargs['product_slug']).order_by('-datetime_created')
    
    def get_serializer_context(self):
        context = {
            'product' : Product.objects.get(slug=self.kwargs['product_slug'])
        }
        return context 