from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer

# comply query optimization 

# product views
# ModelViewSet contains Creat, Retrieve, Update, Destroy and List model mixins
class ProductViewSet(ModelViewSet):
    queryset =  Product.objects.select_related('category').all().order_by('-datetime_created')
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
    serializer_class = CategorySerializer
    lookup_field = 'slug'

    def destroy(self, request, slug):
        category = get_object_or_404(Category.objects.all().annotate(products_count = Count('products')), slug=slug)
        if category.products.count() > 0:
            return Response(f'{category.title} referenced through protected foreign key: Product.', status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        category.delete()
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)