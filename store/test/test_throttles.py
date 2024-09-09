from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from django.contrib.auth.models import Group
from django.conf import settings
from rest_framework.exceptions import ValidationError

from store.test.test_endpoints import MockObjects, GenerateAuthToken
from store.test.helpers.base_helper import UserAuthHelper
from store.throttle import BaseThrottleView


class ThrottleValidationTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_obj = MockObjects()
        self.auth_token =  GenerateAuthToken().generate_auth_token()
        self.view = BaseThrottleView()
        self.valid_group_names = ['Product Manager', 'Content Manager', 'Customer Manager', 'Order Manager']
        self.valid_throttle_scopes = ['anon', 'user', 'product', 'category', 'comment', 'customer', 'address', 'order', 'payment']

        # manager groups
        [Group.objects.create(name=group_name) for group_name in self.valid_group_names]
    
    def test_urls_without_group(self):
        [group.delete() for group in Group.objects.all()]
        
        UserAuthHelper().set_authorization_header(self.api_client, self.auth_token)

        res = self.api_client.get
        responses = [
            res(reverse('product-list')),
            res(reverse('category-list')),
            res(reverse('address-list')),
            res(reverse('order-list'))
        ]
        
        [self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST) for res in responses]
        
    def test_valid_group(self):
        [self.view.validation(group_name, throttle_scope='product') for group_name in self.valid_group_names]
            
    def test_invalid_group(self):    
        invalid_group_name = 'invalid group name'

        with self.assertRaises(ValidationError) as context:
            self.view.validation(
                invalid_group_name, 
                throttle_scope=None
            )
        error_msg = f'Invalid group name: {invalid_group_name}, options are: {self.valid_group_names}'
        self.assertIn(error_msg, str(context.exception))

    def test_valid_throttle_scope(self):
        [self.view.validation(group_name=None, throttle_scope=scope) for scope in self.valid_throttle_scopes]

    def test_invalid_throttle_scope(self):
        invalid_throttle_scope = 'invalid throttle scope'
        with self.assertRaises(ValidationError) as context:
            self.view.validation(
                group_name=None, 
                throttle_scope=invalid_throttle_scope
            )
        error_mes = f"invalid throttle rate: {invalid_throttle_scope}, options are: {self.valid_throttle_scopes}"
        self.assertIn(error_mes ,str(context.exception))
    
    def test_group_name_and_throttle_scope(self):
        self.view.validation(group_name=None, throttle_scope='product')

        with self.assertRaises(ValidationError) as context:
            self.view.validation(
                group_name=self.valid_group_names[0],
                throttle_scope=None
            )
        error_mes = 'throttle_scope attribute has been missing'
        self.assertIn(error_mes ,str(context.exception))
        

class ThrottleRatesTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objects = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.user_auth_helper = UserAuthHelper()
        self.user = self.mock_objects.user_obj
        self.product_url = reverse('product-list')
        self.category_url = reverse('category-list')
        self.comment_url = reverse('product-detail', args=[self.mock_objects.product_obj.slug]) + 'comments/'
        self.cart_url = reverse('cart-list')
        self.cartitems_url =  reverse('cart-detail', args=[self.mock_objects.cart_obj.id]) + 'items/'
        self.customer_url = reverse('customer-list')
        self.customer_info_url = reverse('customer-list') + 'me/'
        self.address_url = reverse('address-list')
        self.order_url = reverse('order-list')
        self.payment_url = reverse('payment-process')
        
        self.default_throttle_rate = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']

        # manager groups
        self.valid_group_names = ['Product Manager', 'Content Manager', 'Customer Manager', 'Order Manager']
        [Group.objects.create(name=group_name) for group_name in self.valid_group_names]
    
    def validation_check(self, throttle_scope, manager_group):
        if throttle_scope is None and manager_group is not None:
            raise ValidationError('throttle_scope attribute is missing', code='invalid')
        
        if throttle_scope is not None and manager_group is None:
            raise ValidationError('manager_group attribute is missing.', code='invalid')
        
        if throttle_scope is None and manager_group is None:
            return True

    def throttle_testing(self, url: str, throttle_scope:str = None, manager_group:Group = None):
        access_level = (
            ('anon', lambda: self.user_auth_helper.unset_authorization_header(self.api_client)),
            ('user', lambda: self.user_auth_helper.set_authorization_header(self.api_client, self.auth_token)),
            (throttle_scope, lambda: self.user_auth_helper.set_or_unset_manager_groups(True, self.user, manager_group)),
        )
        
        reach_any_access_level = False

        for access, config in access_level:
            if access == throttle_scope:
                if self.validation_check(throttle_scope, manager_group):
                    continue

            config()
        
            if self.api_client.get(url).status_code not in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]:
                reach_any_access_level = True

                if access == 'anon':
                    throttle_rate = self.default_throttle_rate[access] = '2/day'
                if access == 'user':
                    throttle_rate = self.default_throttle_rate[access] = '5/day'
                if access == throttle_scope:
                    throttle_rate = self.default_throttle_rate[access] = '7/day'

                for _ in range(int(throttle_rate.split('/')[0]) + 1):
                    response = self.api_client.get(url)
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
        if not reach_any_access_level:
            raise ValueError('No access level succeeded in getting a 200 OK response.')
    
    def test_product_url_throttle(self):
        url = self.product_url
        group = Group.objects.get(name=self.valid_group_names[0])
        self.throttle_testing(url, throttle_scope='product', manager_group=group)
    
    def test_catgory_url_throttle(self):
        url = self.category_url
        group = Group.objects.get(name=self.valid_group_names[0])
        self.throttle_testing(url, throttle_scope='category', manager_group=group)

    def test_comment_url_throttle(self):
        url = self.comment_url
        group = Group.objects.get(name=self.valid_group_names[1])
        self.throttle_testing(url, throttle_scope='comment', manager_group=group)

    def test_cart_url_throttle(self):
        url = self.cart_url
        self.throttle_testing(url, throttle_scope=None, manager_group=None)

    def test_cartitems_url_throttle(self):
        url = self.cartitems_url
        self.throttle_testing(url, throttle_scope=None, manager_group=None)

    def test_customer_url_throttle(self):
        url = self.customer_url
        group = Group.objects.get(name=self.valid_group_names[2]) 
        self.throttle_testing(url, throttle_scope='customer', manager_group=group)

    def test_customer_info_url_throttle(self):
        url = self.customer_info_url
        self.throttle_testing(url, throttle_scope=None ,manager_group=None)

    def test_address_url_throttle(self):
        url = self.customer_url
        group = Group.objects.get(name=self.valid_group_names[2])
        self.throttle_testing(url, throttle_scope='customer', manager_group=group)

    def test_order_url_throttle(self):
        url = self.order_url
        group = Group.objects.get(name=self.valid_group_names[3])
        self.throttle_testing(url, throttle_scope='order', manager_group=group)

    def test_payment_url_anon_and_user_throttle(self):
        url = self.payment_url
        self.throttle_testing(url, throttle_scope=None, manager_group=None)
    
    def test_payment_url_scope_throttle(self):
        self.user_auth_helper.set_authorization_header(self.api_client, self.auth_token)
        url = self.payment_url

        for _ in range(20 + 1):
            response = self.api_client.get(url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
















  