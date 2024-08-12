from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls import resolve

from ..views import CategoryViewSet, ProductViewSet, CommentViewSet, CartViewSet, CartItemViewSet, CustomerViewSet
from ..models import *



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


class GenerateAuthToken:
    def generate_auth_token(self, client, username='username', password='user123'):
        url = reverse('jwt-create')
        # Can not use mock_objs dut to duplicated key value violated unique constraint error , username=username
        credentials = {'username': username, 'password': password}
        response = client.post(url, credentials, format='json')
        if response.status_code == status.HTTP_200_OK:
            try:
                access_token = response.data['access']
                return access_token
            except KeyError:
                raise KeyError(f"'access' key not found in {response.data}")
        raise AssertionError(f'{response.content}')


# Test Cases
class AllowedHttpMethodTests(APITestCase):
    LIST_HTTP_METHODS = ['GET', 'POST', 'OPTIONS', 'HEAD']
    DETAIL_HTTP_METHODS = ['GET', 'OPTIONS', 'HEAD', 'PUT', 'PATCH', 'DELETE']

    def __init__(self, test_case, **kwargs):
        super().__init__()
        self.test_case = test_case
        self.client = APIClient()

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
            self.client.defaults['HTTP_AUTHORIZATION'] = f'JWT {auth_token}'

        response = self.client.options(url)
        if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            raise ValidationError("OPTIONS method not allowed; cannot test allowed HTTP methods.")
        
        self.test_case.assertEqual(response.status_code, status.HTTP_200_OK)

        allowed_methods = response['allow'].split(', ')

        if not expected_methods:
            url_name = resolve(url).url_name
            if 'list' in url_name:
                expected_methods = self.LIST_HTTP_METHODS
            elif 'detail' in url_name:
                expected_methods = self.DETAIL_HTTP_METHODS
        self.test_case.assertEqual(set(allowed_methods), set(expected_methods))


class ProductUrlTests(APITestCase):
    def setUp(self):
        self.mock_objs = MockObjects() # Instantiate MockObjects
        self.allowed_http_methods = AllowedHttpMethodTests(self)
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

    def test_category_list_url(self):
        response = self.client.get(self.category_list_url)
        self.assertTrue(response.json().get('count') > 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_category_detail_url(self):
        response = self.client.get(self.category_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_product_urls_http_methods(self):
        self.allowed_http_methods.check_allowed_methods(self.product_list_url)
        self.allowed_http_methods.check_allowed_methods(self.product_detail_url)
    
    def test_product_urls_resolves(self):
        self.assertEqual(resolve(self.product_list_url).func.cls, ProductViewSet)
        self.assertEqual(resolve(self.product_detail_url).func.cls, ProductViewSet)
    
    def test_product_list_url(self):
        response = self.client.get(self.product_list_url)
        self.assertTrue(response.json().get('count') > 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_product_detail_url(self):                            
        response = self.client.get(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_comment_urls_http_methods(self):
        self.allowed_http_methods.check_allowed_methods(self.comment_list_url)
        self.allowed_http_methods.check_allowed_methods(self.comment_detail_url)

    def test_comment_urls_resolves(self):
        self.assertEqual(resolve(self.comment_list_url).func.cls, CommentViewSet)
        self.assertEqual(resolve(self.comment_detail_url).func.cls, CommentViewSet)
    
    def test_comment_list_url(self):
        response = self.client.get(self.comment_list_url)
        self.assertTrue(response.json().get('count') > 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_comment_detail_url(self):
        response = self.client.get(self.comment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CartUrlTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects() # Instantiate MockObjects
        self.auth_token = GenerateAuthToken().generate_auth_token(client=self.client)
        self.allowed_http_methods = AllowedHttpMethodTests(self)
        self.user = self.mock_objs.user_obj
        self.cart = self.mock_objs.cart_obj
        self.cartitems = self.mock_objs.cartitems_obj
        self.cart_list_url = reverse('cart-list')
        self.cart_detail_url = reverse('cart-detail', args=[self.cart.id])
        self.cartitems_list_url = self.cart_detail_url + 'items/'
        self.cartitems_detail_url = self.cart_detail_url + f'items/{self.cartitems.id}/'

    def test_cart_urls_without_authorization_header(self):
        cart_list_res = self.api_client.get(self.cart_list_url)
        self.assertEqual(cart_list_res.status_code, status.HTTP_401_UNAUTHORIZED)

        cart_detail_res = self.api_client.get(self.cart_detail_url)
        self.assertEqual(cart_detail_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cart_urls_https_methods(self):
        expected_methods = [method.upper() for method in CartViewSet.http_method_names]
        expected_methods.remove('POST')
        self.allowed_http_methods.check_allowed_methods(self.cart_list_url, auth_token=self.auth_token)
        self.allowed_http_methods.check_allowed_methods(self.cart_detail_url, expected_methods=expected_methods, auth_token=self.auth_token)

    def test_cart_urls_resolves(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
        self.assertEqual(resolve(self.cart_list_url).func.cls, CartViewSet)
        self.assertEqual(resolve(self.cart_detail_url).func.cls, CartViewSet)

    def test_cart_list_url(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
        response = self.api_client.get(self.cart_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cart_detail_url(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
        response = self.api_client.get(self.cart_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cartitms_urls_without_authorization_header(self):
        list_url = self.api_client.get(self.cart_list_url)
        self.assertEqual(list_url.status_code, status.HTTP_401_UNAUTHORIZED)

        detail_url = self.api_client.get(self.cart_detail_url)
        self.assertEqual(detail_url.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cartitems_urls_http_methods(self):
        expected_methods =  [method.upper() for method in CartItemViewSet.http_method_names]
        expected_methods.remove('POST')
        self.allowed_http_methods.check_allowed_methods(url=self.cartitems_list_url, auth_token=self.auth_token)
        self.allowed_http_methods.check_allowed_methods(url=self.cartitems_detail_url, expected_methods=expected_methods, auth_token=self.auth_token)

    def test_cartitems_urls_resolves(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
        self.assertEqual(resolve(self.cartitems_list_url).func.cls, CartItemViewSet)
        self.assertEqual(resolve(self.cartitems_detail_url).func.cls, CartItemViewSet)

    def test_cartitems_list_url(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
        response = self.api_client.get(self.cart_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cartitems_detail_url(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
        response = self.api_client.get(self.cartitems_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CustomerUrlTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token(client=self.client)
        self.allowed_http_methods = AllowedHttpMethodTests(self)
        self.user = self.mock_objs.user_obj
        self.customer = self.mock_objs.customer_obj
        self.address = self.mock_objs.address_obj
        self.customer_list_url = reverse('customer-list')
        self.customer_detail_url = reverse('customer-detail', args=[self.customer.id])
        self.customer_info_url = reverse('customer-list') + 'me/'
        self.address_list_url = reverse('address-list')
        self.address_detail_url = reverse('address-detail', args=[self.address.pk])

        self.customer_manager_group = Group.objects.create(name='Customer Manager')

    def set_or_unset_customer_manager_group(self, set_group:bool):
        if set_group == True:
            self.user.groups.set([self.customer_manager_group])
        elif set_group == False:
            self.user.groups.remove(self.customer_manager_group)
    
    def user_to_superuser(self):
        self.user.is_superuser = True
        self.user.save()
    
    # Test Methods
    def test_customer_urls_without_authorization_header(self):
        customer_list_res = self.api_client.get(self.customer_list_url)
        self.assertEqual(customer_list_res.status_code, status.HTTP_401_UNAUTHORIZED)

        customer_detail_res = self.api_client.get(self.customer_detail_url)
        self.assertEqual(customer_detail_res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_urls_http_methods(self):
        self.set_or_unset_customer_manager_group(set_group=True)
        expected_methods = [method.upper() for method in CustomerViewSet.http_method_names]
        expected_methods.remove('PUT')
        self.allowed_http_methods.check_allowed_methods(url=self.customer_list_url, expected_methods=expected_methods, auth_token=self.auth_token)

        expected_methods.append('PUT')
        self.allowed_http_methods.check_allowed_methods(url=self.customer_detail_url, expected_methods=expected_methods, auth_token=self.auth_token)

    def test_customer_urls_resolves(self):
        self.assertEqual(resolve(self.customer_list_url).func.cls, CustomerViewSet)
        self.assertEqual(resolve(self.customer_detail_url).func.cls, CustomerViewSet)        

    def test_customer_list_url_different_users_access(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'

        response = self.api_client.get(self.customer_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        self.set_or_unset_customer_manager_group(set_group=True)
        response = self.api_client.get(self.customer_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.set_or_unset_customer_manager_group(set_group=False)
        self.user_to_superuser()
        response = self.api_client.get(self.customer_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_customer_detail_url_different_users_access(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
        
        response = self.api_client.get(self.customer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        self.set_or_unset_customer_manager_group(set_group=True)
        response = self.api_client.get(self.customer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.set_or_unset_customer_manager_group(set_group=False)
        self.user_to_superuser()
        response = self.api_client.get(self.customer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_info_url_without_authorization_header(self):
        response = self.api_client.get(self.customer_info_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_customer_info_url_http_methods(self):
        expected_methods = ['GET', 'PUT', 'HEAD', 'OPTIONS']
        self.allowed_http_methods.check_allowed_methods(url=self.customer_info_url, expected_methods=expected_methods, auth_token=self.auth_token)

    def test_customer_info_url_resolves(self):
        self.assertEqual(resolve(self.customer_info_url).func.cls, CustomerViewSet)

    def test_customer_info_url(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
        response = self.api_client.get(self.customer_info_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
