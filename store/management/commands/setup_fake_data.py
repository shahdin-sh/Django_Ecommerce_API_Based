# setup_test_data.py
from config import settings
import factory
import random

from datetime import datetime, timedelta
from factory.fuzzy import FuzzyDateTime
from faker import Faker

from django.contrib.auth import get_user_model 
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.timezone import get_current_timezone
from django.utils.timezone import make_aware

from store.models import Address, Cart, CartItem, Category, Comment, Order, OrderItem, Product, Discount, Customer
from store.factories import (
    CartFactory,
    CategoryFactory,
    CommentFactory,
    OrderItemFactory,
    ProductFactory,
    DiscountFactory,
    CustomerFactory,
    AddressFactory,
    OrderFactory,
    CartItemFactory,
    UserFactory
)

faker = Faker()

User = get_user_model()

list_of_models = [CartItem, Cart, OrderItem, Order, Product, Category, Comment, Discount, Address, Customer]

NUM_CATEGORIES = 100
NUM_DISCOUNTS = 10
NUM_PRODUCTS = 1000
NUM_ORDERS = 30
NUM_CARTS = 100
NUM_USERS = 20

class Command(BaseCommand):
    help = "Generates fake data"

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting old data...")
        models = list_of_models
        for model in models:
            model.objects.all().delete()
        [user.delete() for user in User.objects.exclude(is_superuser=True)]
        self.stdout.write("Creating new data...\n")

        tz = timezone.get_current_timezone()

        # users data
        print(f"Adding {NUM_USERS} users...", end='')
        all_users = [UserFactory() for _ in range(NUM_USERS)]
        print('DONE')

        # users groups
        print(f"Adding groups to half of the users ")
        randomized_users = random.sample(list(all_users), int(NUM_USERS / 2))
        group_name_list = ['Product Manager', 'Content Manager', 'Customer Manager', 'Order Manager']

        for user in randomized_users:
            random_group_name = random.choice(group_name_list)
            group = Group.objects.get(name=random_group_name)
            user.groups.set([group])

            user.is_staff = True
            user.save()

        # Categories data
        print(f"Adding {NUM_CATEGORIES} categories...", end='')
        all_categories = [CategoryFactory(top_product=None) for _ in range(NUM_CATEGORIES)]
        print('DONE')
        
        # Discounts data
        print(f"Adding {NUM_DISCOUNTS} discounts...", end='')
        all_discounts = [DiscountFactory() for _ in range(NUM_DISCOUNTS)]
        print('DONE')

        # Products data
        print(f"Adding {NUM_PRODUCTS} product...", end='')
        all_products = list()
        for _ in range(NUM_PRODUCTS):
            new_product = ProductFactory(category_id=random.choice(all_categories).id)
            new_product.datetime_created = datetime(random.randrange(2019, 2023),random.randint(1,12),random.randint(1,12), tzinfo=timezone.utc)
            new_product.datetime_modified = new_product.datetime_created + timedelta(hours=random.randint(1, 500))
            new_product.save()
            all_products.append(new_product)
        print('DONE')

        # Customers data
        print(f"customers created when normal user created...", end='')
        # customer instance will create for newly created user via signal
        all_customers = Customer.objects.all()
        print('DONE')

        # Addresses data
        print(f"Adding customers addresses...", end='')
        for customer in all_customers:
            AddressFactory(customer=customer)
        print('DONE')

        # Orders data
        print(f"Adding {NUM_ORDERS} orders...", end='')
        all_orders = [OrderFactory(
            customer_id=random.choice(all_customers).id
        ) for _ in range(NUM_ORDERS)]
        for order in all_orders:
            order.datetime_created =  datetime(random.randrange(2019, 2023),random.randint(1,12),random.randint(1,12), tzinfo=timezone.utc)
            order.save()
        print('DONE')

        # OrderItems data
        print(f"Adding order items...", end='')
        all_order_items = list()
        for order in all_orders:
            products = random.sample(all_products, random.randint(1, 10))
            for product in products:
                order_item = OrderItemFactory(
                    order_id=order.id,
                    product_id=product.id,
                    unit_price=product.unit_price,
                )
                all_order_items.append(order_item)
        print('DONE')

        # Comments data
        print(f"Adding product comments...", end='')
        for product in all_products:
            for _ in range(random.randint(1, 10)):
                comment = CommentFactory(product_id=product.id)
                comment.datetime_created = datetime(random.randrange(2019, 2023),random.randint(1,12),random.randint(1,12), tzinfo=timezone.utc)
                comment.save()
        print('DONE')

        # Carts data
        print(f"Adding {NUM_CARTS} carts...", end='')
        all_carts = [CartFactory() for _ in range(NUM_CARTS)]
        print('DONE')

        # CartItems data
        print(f"Adding cart items...", end='')
        for cart in all_carts:
            products = random.sample(all_products, random.randint(1, 10))
            for product in products:
                cart_item = CartItemFactory(
                    cart_id=cart.id,
                    product_id=product.id,
                )
                cart.items.set([cart_item])
        print('DONE')