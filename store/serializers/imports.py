from rest_framework import serializers
from rest_framework.reverse import reverse

from django.db import transaction 
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.text import slugify

from config.urls import SITE_URL_HOST


from ..models import Product, Category, Comment, Cart, CartItem, Customer, Address, Order, OrderItem, Wishlist
from ..validations import quantity_validation
