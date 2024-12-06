from django.urls import path, include
from rest_framework_nested import routers
from .views import (
    ProductViewSet,
    CategoryViewSet,
    WishlistViewSet,
    CartViewSet, 
    CustomerViewSet,
    AddressViewSet,
    OrderViewSet,
    CommentViewSet,
    AddToCartView,
    AddToWishlistView,
    CartItemViewSet,
    WishlistProductView,
    PaymentProcessView
)


router = routers.DefaultRouter()

router.register('products', ProductViewSet, basename='product') # product-list| product-detail
router.register('categories', CategoryViewSet, basename='category') # category-list | category-detail
router.register('wishlist', WishlistViewSet, basename='wishlist') # wishlist-list | wishlist-detail
router.register('carts', CartViewSet, basename='cart') # cart-list | cart-detail
router.register('customers', CustomerViewSet, basename='customer') # customer-list | customer-detail
router.register('addresses', AddressViewSet, basename='address') # address-list | address-detail
router.register('orders', OrderViewSet, basename='order') # order-list | order-view

product_router = routers.NestedDefaultRouter(router, 'products', lookup='product') # products/product_slug
product_router.register('comments', CommentViewSet, basename='product-comments') # products/product_slug/comments/pk
product_router.register('add-to-cart', AddToCartView, basename='product-add-to-cart') # products/product_slug/add-to-cart
product_router.register('add-to-wishlist', AddToWishlistView, basename='product-add-to-wishlist') # products/product_slug/add-to-wishlist

cart_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart') # carts/uuid 
cart_router.register('items', CartItemViewSet, basename='cart-items') # carts/uuid/items/item_pk

wishlist_router = routers.NestedDefaultRouter(router, 'wishlist', lookup='wishlist') # wishlist/id
wishlist_router.register('products', WishlistProductView, basename='wishlist-products') # wishlist/id/products/product_id


urlpatterns = [
    path('', include(router.urls)),
    path('payment', PaymentProcessView.as_view(), name='payment-process'),
] + product_router.urls + cart_router.urls + wishlist_router.urls
