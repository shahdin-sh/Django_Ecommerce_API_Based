from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, User

from store.models import (
    Category,
    Product,
    Comment,
    Cart,
    CartItem,
    Customer,
    Address,
    Order,
    OrderItem
)


class MockObjects:
    def __init__(self):
        self.user_obj = get_user_model().objects.create_user(
            username = 'username',
            email = 'username@gmail.com',
            password = 'user123',
            is_active = True,
        )
        self.category_obj =  Category.objects.create(
            title = 'category',
            slug = 'category'
        )
        self.product_obj = Product.objects.create(
            name = 'product',
            category = self.category_obj,
            slug = 'product',
            unit_price =  '100000',
            inventory = 10, 
        )
        self.comment_obj = Comment.objects.create(
            product = self.product_obj,
            name = 'comment',
            body = 'random text for comment',
            status = Comment.COMMENT_STATUS_APPROVED
        )
        self.cart_obj = Cart.objects.create(
            id = 'a2dbc6a6-27bc-4165-8520-2d151fe8b357',
        )
        self.cartitems_obj = CartItem.objects.create(
            cart = self.cart_obj,
            product = self.product_obj,
            quantity = 12
        )
        self.customer_obj = Customer.objects.get(user=self.user_obj)
        self.address_obj = Address.objects.create(
            customer = self.customer_obj,
            province = 'province A',
            city = 'city B',
            street = 'street number 1'
        )
        self.order_obj = Order.objects.create(
            customer = self.customer_obj,
            status = Order.ORDER_STATUS_UNPAID
        )
        self.orderitems_obj = OrderItem.objects.create(
            order = self.order_obj,
            product = self.product_obj,
            quantity = 3,
            unit_price = self.cartitems_obj.product.unit_price
        )


class GenerateAuthToken:
    def __init__(self):
        super().__init__()
        self.api_client = APIClient()

    def generate_auth_token(self, username='username', password='user123'):
        url = reverse('jwt-create')
        # Can not use mock_objs dut to duplicated key value violated unique constraint error , username=username
        credentials = {'username': username, 'password': password}
        response = self.api_client.post(url, credentials, format='json')
        if response.status_code == status.HTTP_200_OK:
            try:
                access_token = response.data['access']
                return access_token
            except KeyError:
                raise KeyError(f"'access' key not found in {response.data}")
        raise AssertionError(f'{response.content} | {response.status_code}')


class UserAuthHelper():
    def set_or_unset_manager_groups(self, set_group:bool, user:User, manager_group:Group):
        if set_group:
            user.groups.set([manager_group])
        else:
            user.groups.remove(manager_group)
    
    def set_authorization_header(self, api_client:APIClient , auth_token):
        api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {auth_token}'
    
    def unset_authorization_header(self, api_client:APIClient):
        api_client.defaults.pop('HTTP_AUTHORIZATION', None)

    def set_to_superuser(self, set_superuser:bool, user:object):
        if set_superuser:
            user.is_superuser = True
        else:
            user.is_superuser = False
        user.save()