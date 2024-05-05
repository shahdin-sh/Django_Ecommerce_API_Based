from . import views
from django.urls import path, include

from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework_nested import routers

router = routers.DefaultRouter()

router.register('products', views.ProductViewSet, basename='product') # product-list| product-detail
router.register('categories', views.CategoryViewSet, basename='category') # category-list | category-detail

product_router = routers.NestedDefaultRouter(router, 'products', lookup='product') # products/product_slug
product_router.register('comments', views.CommentViewSet, basename='product-comments') # products/product_slug/comments/pk

urlpatterns = [path('', include(router.urls)),] + product_router.urls
