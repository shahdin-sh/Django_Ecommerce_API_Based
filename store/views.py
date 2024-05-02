from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.http import HttpResponse

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import Product, Category, OrderItem
from .serializers import ProductSerializer, CategorySerializer

# comply query optimization 

def product_list_via_api(request):
    if request.method == 'GET':
        products_queryset = Product.objects.select_related('category').all().order_by('-datetime_created')
        serializer = ProductSerializer(products_queryset, many=True, context={'request': request})

        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save() 
        return Response(status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
def product_detail_via_api(request, slug):
    product = get_object_or_404(Product.objects.select_related('category').all(), slug=slug)
    if request.method == 'GET':
        serializer = ProductSerializer(product, context={'request': request})

        return Response(serializer.data)
    elif request.method == 'PUT':
        serializer = ProductSerializer(product, request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(f'{product.name} updated successfully.', status=status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        if product.order_items.count() > 0:
            return Response(f'{product.name} referenced through protected foreign key: OrderItem', status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        product.delete()
        return Response(status=status.HTTP_404_NOT_FOUND)


# category views
@api_view(['GET', 'POST'])
def category_list_via_api(request):
    if request.method == 'GET':
        category_queryset = Category.objects.all().annotate(
            products_count = Count('products')
        )
        serializer = CategorySerializer(category_queryset, many=True, context={'request': request})

        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

@api_view(['GET', 'PUT', 'DELETE'])
def category_detail_via_api(request, slug):
    category = get_object_or_404(Category.objects.all().annotate(products_count = Count('products')), slug=slug)
    if request.method == 'GET':
        serializer = CategorySerializer(category,  context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = CategorySerializer(category, data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'DELETE':
        if category.products.count() > 0:
            return Response(f'{category.title} referenced through protected foreign key: Product.', status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
        category.delete()
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)
