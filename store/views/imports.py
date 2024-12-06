import requests
import json

from celery import group
from django_filters.rest_framework import DjangoFilterBackend
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet

from ..filters import ProductFilter, OrderFilter, CustomerWithOutAddress
from ..paginations import StandardResultSetPagination, LargeResultSetPagination
from ..permissions import IsProductManager, IsContentManager, IsCustomerManager, IsOrderManager 
from ..throttle import BaseThrottleView
from ..models import (
    Product, 
    Category, 
    Comment, 
    Cart, 
    Wishlist,
    CartItem, 
    Customer,
    Address, 
    Order, 
    OrderItem,
)
from ..tasks import (
    approve_order_status_after_successful_payment,
    update_inventory, 
    change_anon_cart_to_auth_cart,
    transit_anon_cart_items_to_auth_cart_and_delete,
)
from ..serializers import (
    CategorySerializer,
    CommentSerializer,
    ProductSerializer,
    WishlistProductSerializer,
    WishlistSerializer,
    ManagerAddItemtoCartSerializer,
    ManagerCartItemSerializer,
    ManagerCartSerializer,
    AddItemtoCartSerializer,
    CartItemSerializer,
    CartSerializer,
    AddressSerializer,
    AddAddressSerializer,
    ManagerAddressSerializer,
    ManagersAddAddressSerializer,
    ManagerCustomerSerializer,
    CustomerSerializer,
    OrderCreationSerializer,
    OrderSerializer,
    ManagerOrderSerializer,
    PaymentSerializer
)

# Determines the appropriate throttle class based on throttle_scopes and four types of user 
# inlucding: superusers, managers, anonymous users and authenticated users.
base_throttle = BaseThrottleView()