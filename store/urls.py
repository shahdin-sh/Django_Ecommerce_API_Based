from . import views
from django.urls import path, include

from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework_nested import routers

router = routers.DefaultRouter()

router.register('products', views.ProductViewSet, basename='product') # product-list| product-detail
router.register('categories', views.CategoryViewSet, basename='category') # category-list | category-detail
router.register('carts', views.CartViewSet, basename='cart') # cart-list | cart-detail
router.register('customers', views.CustomerViewSet, basename='customer') # customer-list | customer-detail
router.register('addresses', views.AdressViewSet, basename='address') # address-list | address-detail
router.register('orders', views.OrderViewSet, basename='order') # order-list | order-view

product_router = routers.NestedDefaultRouter(router, 'products', lookup='product') # products/product_slug
product_router.register('comments', views.CommentViewSet, basename='product-comments') # products/product_slug/comments/pk

cart_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart') # carts/uuid 
cart_router.register('items', views.CartItemViewSet, basename='cart-items') # carts/uuid/items/item_pk




urlpatterns = [
    path('', include(router.urls)),
] + product_router.urls + cart_router.urls
