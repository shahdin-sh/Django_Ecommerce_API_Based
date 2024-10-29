from . import views
from django.urls import path, include

from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework_nested import routers

router = routers.DefaultRouter()

router.register('products', views.ProductViewSet, basename='product') # product-list| product-detail
router.register('categories', views.CategoryViewSet, basename='category') # category-list | category-detail
router.register('wishlist', views.WishlistViewSet, basename='wishlist') # wishlist-list | wishlist-detail
router.register('carts', views.CartViewSet, basename='cart') # cart-list | cart-detail
router.register('customers', views.CustomerViewSet, basename='customer') # customer-list | customer-detail
router.register('addresses', views.AddressViewSet, basename='address') # address-list | address-detail
router.register('orders', views.OrderViewSet, basename='order') # order-list | order-view

product_router = routers.NestedDefaultRouter(router, 'products', lookup='product') # products/product_slug
product_router.register('comments', views.CommentViewSet, basename='product-comments') # products/product_slug/comments/pk
product_router.register('add-to-cart', views.AddToCartViewSet, basename='product-add-to-cart') # products/product_slug/add-to-cart
product_router.register('add-to-wishlist', views.AddToWishlist, basename='product-add-to-wishlist') # products/product_slug/add-to-wishlist

cart_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart') # carts/uuid 
cart_router.register('items', views.CartItemViewSet, basename='cart-items') # carts/uuid/items/item_pk

wishlist_router = routers.NestedDefaultRouter(router, 'wishlist', lookup='wishlist') # wishlist/id
wishlist_router.register('products', views.WishlistProductViewSet, basename='wishlist-products') # wishlist/id/products/product_id


urlpatterns = [
    path('', include(router.urls)),
    path('payment', views.PaymentProcess.as_view(), name='payment-process'),
] + product_router.urls + cart_router.urls + wishlist_router.urls
