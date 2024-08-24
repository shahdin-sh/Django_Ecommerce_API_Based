from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls import resolve

from .helpers.base_helper import BaseHelper
from .helpers.endpoints_access_helper import ApiEndpointsAccessHelper

from ..models import (
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
from ..views import (
    CategoryViewSet, 
    ProductViewSet, 
    CommentViewSet, 
    CartViewSet, 
    CartItemViewSet, 
    CustomerViewSet,
    AddressViewSet,
    OrderViewSet,
    PaymentProcess
)


User = get_user_model()


class MockObjects:
    def __init__(self):
        self.user_obj = User.objects.create_user(
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


#  Test Cases
class AllowedHttpMethodTests(APITestCase):
    LIST_HTTP_METHODS = ['GET', 'POST', 'OPTIONS', 'HEAD']
    DETAIL_HTTP_METHODS = ['GET', 'OPTIONS', 'HEAD', 'PUT', 'PATCH', 'DELETE']

    def __init__(self):
        super().__init__()
        self.api_client = APIClient()

    def check_allowed_methods(self, url: str, expected_methods: list = None, auth_token: str = None):
        """
        Check if the allowed HTTP methods for a given URL match the expected methods.

        Parameters:
        - url (str): The URL to test.
        - expected_methods (list): A list of HTTP methods expected to be allowed.
        - auth_token (str): Optional JWT token for authentication.

        Raises:
        - ValidationError: If OPTIONS method is not allowed or unexpected response status.
        """
        if auth_token:
            self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {auth_token}'

        response = self.api_client.options(url)
        if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            raise ValidationError("OPTIONS method not allowed; cannot test allowed HTTP methods.")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        allowed_methods = response['allow'].split(', ')

        if not expected_methods:
            url_name = resolve(url).url_name
            if 'list' in url_name:
                expected_methods = self.LIST_HTTP_METHODS
            elif 'detail' in url_name:
                expected_methods = self.DETAIL_HTTP_METHODS
        self.assertEqual(set(allowed_methods), set(expected_methods))


class ProductUrlsTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()  
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.allowed_http_methods = AllowedHttpMethodTests()
        self.endpoint_acess_helper = ApiEndpointsAccessHelper(self)
        self.user = self.mock_objs.user_obj
        self.category = self.mock_objs.category_obj
        self.product = self.mock_objs.product_obj
        self.comment = self.mock_objs.comment_obj
        self.category_list_url = reverse('category-list')
        self.category_detail_url = reverse('category-detail', args=[self.category.slug])
        self.product_list_url = reverse('product-list')
        self.product_detail_url = reverse('product-detail', args=[self.product.slug])
        self.comment_list_url = reverse('product-detail', args=[self.product.slug]) + 'comments/'
        self.comment_detail_url = reverse('product-detail', args=[self.product.slug]) + f'comments/{self.comment.id}/'
        #  Create a user group to ensure throttling and permissions are correctly applied in tests. 
        #  The test environment mirrors the actual conditions under which the URL paths are accessed.
        self.product_manager_group = Group.objects.create(name='Product Manager')
        self.comment_manager_group = Group.objects.create(name='Content Manager')

    def test_category_urls_http_methods(self):
        self.allowed_http_methods.check_allowed_methods(self.category_list_url)
        self.allowed_http_methods.check_allowed_methods(self.category_detail_url)

    def test_category_urls_resolves(self):
        self.assertEqual(resolve(self.category_list_url).func.cls, CategoryViewSet)
        self.assertEqual(resolve(self.category_detail_url).func.cls, CategoryViewSet)

    def test_category_urls_access(self):
        list_url = self.category_list_url
        self.endpoint_acess_helper.urls_method_access_test(list_url, 'product', 
            self.auth_token, self.user, self.product_manager_group
        )

        detail_url = self.category_detail_url
        self.endpoint_acess_helper.urls_method_access_test(detail_url, 'product', 
            self.auth_token, self.user, self.product_manager_group
        )

    def test_product_urls_http_methods(self):
        self.allowed_http_methods.check_allowed_methods(self.product_list_url)
        self.allowed_http_methods.check_allowed_methods(self.product_detail_url)
    
    def test_product_urls_resolves(self):
        self.assertEqual(resolve(self.product_list_url).func.cls, ProductViewSet)
        self.assertEqual(resolve(self.product_detail_url).func.cls, ProductViewSet)
       
    def test_product_urls_access(self):
        list_url = self.product_list_url
        self.endpoint_acess_helper.urls_method_access_test(list_url, 'product', 
            self.auth_token, self.user, self.product_manager_group
        )

        detail_url = self.product_detail_url
        self.endpoint_acess_helper.urls_method_access_test(detail_url, 'product', 
            self.auth_token, self.user, self.product_manager_group
        )

    def test_comment_urls_http_methods(self):
        self.allowed_http_methods.check_allowed_methods(self.comment_list_url)
        self.allowed_http_methods.check_allowed_methods(self.comment_detail_url)

    def test_comment_urls_resolves(self):
        self.assertEqual(resolve(self.comment_list_url).func.cls, CommentViewSet)
        self.assertEqual(resolve(self.comment_detail_url).func.cls, CommentViewSet)
    
    def test_comment_urls_access(self):
        list_url = self.comment_list_url
        self.endpoint_acess_helper.urls_method_access_test(list_url, 'comment', 
            self.auth_token, self.user, self.comment_manager_group
        )

        detail_url = self.comment_detail_url
        self.endpoint_acess_helper.urls_method_access_test(detail_url, 'comment', 
            self.auth_token, self.user, self.comment_manager_group
        )


class CartUrlsTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.base_helper = BaseHelper()
        self.mock_objs = MockObjects() # Instantiate MockObjects
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.allowed_http_methods = AllowedHttpMethodTests()
        self.endpoint_acess_helper = ApiEndpointsAccessHelper(self)
        self.user = self.mock_objs.user_obj
        self.cart = self.mock_objs.cart_obj
        self.cartitems = self.mock_objs.cartitems_obj
        self.cart_list_url = reverse('cart-list')
        self.cart_detail_url = reverse('cart-detail', args=[self.cart.id])
        self.cartitems_list_url = self.cart_detail_url + 'items/'
        self.cartitems_detail_url = self.cart_detail_url + f'items/{self.cartitems.id}/'
    
    # Test Methods
    def test_cart_urls_https_methods(self):
        expected_methods = [method.upper() for method in CartViewSet.http_method_names]
        expected_methods.remove('POST')
        self.allowed_http_methods.check_allowed_methods(self.cart_list_url, auth_token=self.auth_token)
        self.allowed_http_methods.check_allowed_methods(self.cart_detail_url, expected_methods=expected_methods, auth_token=self.auth_token)

    def test_cart_urls_resolves(self):
        self.base_helper.set_authorization_header(self.api_client, self.auth_token)
        self.assertEqual(resolve(self.cart_list_url).func.cls, CartViewSet)
        self.assertEqual(resolve(self.cart_detail_url).func.cls, CartViewSet)
  
    def test_cart_urls_access(self):
        list_url = self.cart_list_url
        self.endpoint_acess_helper.urls_method_access_test(list_url, 'cart', 
            self.auth_token, self.user, manager_group=None
        )

        detail_url = self.cart_detail_url
        self.endpoint_acess_helper.urls_method_access_test(detail_url, 'cart', 
            self.auth_token, self.user, manager_group=None
        )

    def test_cartitems_urls_http_methods(self):
        expected_methods =  [method.upper() for method in CartItemViewSet.http_method_names]
        expected_methods.remove('POST')
        self.allowed_http_methods.check_allowed_methods(url=self.cartitems_list_url, auth_token=self.auth_token)
        self.allowed_http_methods.check_allowed_methods(url=self.cartitems_detail_url, expected_methods=expected_methods, auth_token=self.auth_token)

    def test_cartitems_urls_resolves(self):
        self.base_helper.set_authorization_header(self.api_client, self.auth_token)
        self.assertEqual(resolve(self.cartitems_list_url).func.cls, CartItemViewSet)
        self.assertEqual(resolve(self.cartitems_detail_url).func.cls, CartItemViewSet)

    def test_cartitems_urls_access(self):
        list_url = self.cartitems_list_url
        self.endpoint_acess_helper.urls_method_access_test(list_url, 'cartitems', 
            self.auth_token, self.user, manager_group=None
        )

        detail_url = self.cartitems_list_url
        self.endpoint_acess_helper.urls_method_access_test(detail_url, 'cartitems', 
            self.auth_token, self.user, manager_group=None
        )

class CustomerUrlsTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.base_helper = BaseHelper()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.allowed_http_methods = AllowedHttpMethodTests()
        self.endpoint_acess_helper = ApiEndpointsAccessHelper(self)
        self.user = self.mock_objs.user_obj
        self.customer = self.mock_objs.customer_obj
        self.address = self.mock_objs.address_obj
        self.customer_list_url = reverse('customer-list')
        self.customer_detail_url = reverse('customer-detail', args=[self.customer.id])
        self.customer_info_url = reverse('customer-list') + 'me/'
        self.address_list_url = reverse('address-list')
        self.address_detail_url = reverse('address-detail', args=[self.address.pk])

        self.customer_manager_group = Group.objects.create(name='Customer Manager')

    def test_customer_urls_without_authorization_header(self):
        customer_list_res = self.api_client.get(self.customer_list_url)
        self.assertEqual(customer_list_res.status_code, status.HTTP_401_UNAUTHORIZED)

        customer_detail_res = self.api_client.get(self.customer_detail_url)
        self.assertEqual(customer_detail_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_urls_http_methods(self):
        self.base_helper.set_or_unset_manager_groups(True, self.user ,self.customer_manager_group)
        expected_methods = [method.upper() for method in CustomerViewSet.http_method_names]
        expected_methods.remove('PUT')
        self.allowed_http_methods.check_allowed_methods(url=self.customer_list_url, expected_methods=expected_methods, auth_token=self.auth_token)

        expected_methods.append('PUT')
        self.allowed_http_methods.check_allowed_methods(url=self.customer_detail_url, expected_methods=expected_methods, auth_token=self.auth_token)

    def test_customer_urls_resolves(self):
        self.assertEqual(resolve(self.customer_list_url).func.cls, CustomerViewSet)
        self.assertEqual(resolve(self.customer_detail_url).func.cls, CustomerViewSet)        

    def test_customer_urls_access(self):
        list_url = self.customer_list_url
        self.endpoint_acess_helper.urls_method_access_test(list_url, 'customer', 
            self.auth_token, self.user, self.customer_manager_group
        )

        detail_url = self.customer_detail_url
        self.endpoint_acess_helper.urls_method_access_test(detail_url, 'customer', 
            self.auth_token, self.user, self.customer_manager_group
        )
    
    def test_customer_info_url_without_authorization_header(self):
        response = self.api_client.get(self.customer_info_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_info_url_http_methods(self):
        expected_methods = ['GET', 'PUT', 'HEAD', 'OPTIONS']
        self.allowed_http_methods.check_allowed_methods(url=self.customer_info_url, expected_methods=expected_methods, auth_token=self.auth_token)

    def test_customer_info_url_resolves(self):
        self.assertEqual(resolve(self.customer_info_url).func.cls, CustomerViewSet)

    def test_customer_info_url_access(self):
        url = self.customer_info_url
        self.endpoint_acess_helper.urls_method_access_test(url, 'customer_info', 
            self.auth_token, self.user, self.customer_manager_group
        )
    
    def test_address_urls_without_authorization_header(self):
        address_list_res = self.api_client.get(self.address_list_url)
        self.assertEqual(address_list_res.status_code, status.HTTP_401_UNAUTHORIZED)

        address_detail_res = self.api_client.get(self.address_detail_url)
        self.assertEqual(address_detail_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_address_urls_http_methods(self):
        self.allowed_http_methods.check_allowed_methods(url=self.address_list_url, auth_token=self.auth_token)
        self.allowed_http_methods.check_allowed_methods(url=self.address_detail_url, auth_token=self.auth_token)        

    def test_address_urls_resolves(self):
        self.assertEqual(resolve(self.address_list_url).func.cls, AddressViewSet)
        self.assertEqual(resolve(self.address_detail_url).func.cls, AddressViewSet)     

    def test_address_urls_access(self):
        list_url = self.address_list_url
        self.endpoint_acess_helper.urls_method_access_test(list_url, 'address', 
            self.auth_token, self.user, self.customer_manager_group
        )

        detail_url = self.address_detail_url
        self.endpoint_acess_helper.urls_method_access_test(detail_url, 'address', 
            self.auth_token, self.user, self.customer_manager_group
        )
    
    
class OrderUrlsTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.allowed_http_methods = AllowedHttpMethodTests()
        self.endpoint_acess_helper = ApiEndpointsAccessHelper(self)
        self.user = self.mock_objs.user_obj
        self.order = self.mock_objs.order_obj
        self.orderitems = self.mock_objs.orderitems_obj
        self.order_list_url = reverse('order-list')
        self.order_detail_url = reverse('order-detail', args=[self.order.id])

        self.order_manager_group = Group.objects.create(name='Order Manager')
    
    def set_authorization_header(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
    
    # Test Methods
    def test_order_urls_without_authorization_header(self):
        order_list_res = self.api_client.get(self.order_list_url)
        self.assertEqual(order_list_res.status_code, status.HTTP_401_UNAUTHORIZED)

        order_detail_res = self.api_client.get(self.order_detail_url)
        self.assertEqual(order_detail_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_order_urls_http_methods(self):
        self.allowed_http_methods.check_allowed_methods(url=self.order_list_url, auth_token=self.auth_token)
        self.allowed_http_methods.check_allowed_methods(url=self.order_detail_url, auth_token=self.auth_token)        

    def test_order_urls_resolves(self):
        self.assertEqual(resolve(self.order_list_url).func.cls, OrderViewSet)
        self.assertEqual(resolve(self.order_detail_url).func.cls, OrderViewSet)     

    def test_order_urls_access(self):
        list_url = self.order_list_url
        self.endpoint_acess_helper.urls_method_access_test(list_url, 'order', 
            self.auth_token, self.user, self.order_manager_group
        )

        detail_url = self.order_detail_url
        self.endpoint_acess_helper.urls_method_access_test(detail_url, 'order', 
            self.auth_token, self.user, self.order_manager_group
        )
   
    def test_orderitems_urls_access(self):
        list_url = self.order_detail_url + 'items/'
        response = self.api_client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        detail_url = self.order_detail_url + f'items/{self.orderitems.id}'
        response = self.api_client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    

class PaymentUrlsTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.allowed_http_methods  = AllowedHttpMethodTests()
        self.endpoint_acess_helper = ApiEndpointsAccessHelper(self)
        self.user = self.mock_objs.user_obj
        self.payment_url = reverse('payment-process')
    
    # Test Methods       
    # def test_payment_url_http_methods(self):
    #     self.allowed_http_methods.check_allowed_methods(url=self.payment_url, auth_token=self.auth_token)
    
    def test_payment_url_resolves(self):
        self.assertEqual(resolve(self.payment_url).func.cls, PaymentProcess)
    
    def test_payment_urls_access(self):
        url = self.payment_url
        self.endpoint_acess_helper.urls_method_access_test(self.payment_url, 'payment', 
            self.auth_token, self.user, manager_group=None
        )