from . import views
from django.urls import path, include

from rest_framework.routers import SimpleRouter, DefaultRouter

router = DefaultRouter()

router.register('products', views.ProductViewSet, basename='product') # product-list| product-detail
router.register('categories', views.CategoryViewSet, basename='category') # category-list | category-detail


urlpatterns = [
    path('', include(router.urls))
]

# urlpatterns = [
#     path('product_list', views.ProductListView.as_view(), name='product_list' ),
#     path('product/<slug:slug>', views.ProductDetailView.as_view(), name='product_detail'),
#     path('category_list', views.CategoryListView.as_view(), name='category_list'),
#     path('category/<slug:slug>', views.CategoryDetailView.as_view(), name='category_detail'),
# ]
