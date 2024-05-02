from . import views
from django.urls import path

urlpatterns = [
    path('product_list', views.product_list_via_api, name='product_list' ),
    path('product/<slug:slug>', views.product_detail_via_api, name='product_detail'),
    path('category_list', views.category_list_via_api, name='category_list'),
    path('category/<slug:slug>', views.category_detail_via_api, name='category_detail'),
]
