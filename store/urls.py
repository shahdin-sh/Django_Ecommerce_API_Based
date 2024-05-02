from . import views
from django.urls import path

urlpatterns = [
    path('product_list', views.ProductListView.as_view(), name='product_list' ),
    path('product/<slug:slug>', views.ProductDetailView.as_view(), name='product_detail'),
    path('category_list', views.CategoryListView.as_view(), name='category_list'),
    path('category/<slug:slug>', views.CategoryDetailView.as_view(), name='category_detail'),
]
