from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient

from django.urls import resolve
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from ..views import CategoryViewSet, ProductViewSet, CommentViewSet, CartViewSet, CartItemViewSet
from ..models import *



User = get_user_model()


class MockObjects:
    def __init__(self):
        self.user_obj = User.objects.create_user(
            username = 'username',
            email = 'username@gmail.com',
            password = 'user123',
            is_active=True,
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


class GenerateAuthToken:
    def generate_auth_token(self, client):
        url = reverse('jwt-create')
        # Can not use mock_objs dut to duplicated key value violated unique constraint error , username=username
        credentials = {'username': 'username', 'password': 'user123'}
        response = client.post(url, credentials, format='json')
        access_token = response.data['access']
        return access_token


# Test Cases
class AllowedHttpMethodTests(APITestCase):
    def __init__(self, test_case):
        self.test_case = test_case
        self.all_http_methods = ['GET', 'POST', 'OPTIONS', 'HEAD']

    def check_allowed_methods(self, url, expected_methods:None):
        response = self.test_case.client.options(url)
        self.test_case.assertEqual(response.status_code, status.HTTP_200_OK)
        allowed_methods = response['allow'].split(', ')
        if expected_methods is None:
            expected_methods = self.all_http_methods
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
        url = self.category_list_url
        self.allowed_http_methods.check_allowed_methods(url, expected_methods=None)

    def test_category_url_resolves(self):
        url = self.category_list_url
        self.assertEqual(resolve(url).func.cls, CategoryViewSet)

    def test_category_list_url(self):
        response = self.client.get(self.category_list_url)
        self.assertTrue(response.json().get('count') > 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_category_detail_url(self):
        response = self.client.get(self.category_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_product_urls_http_methods(self):
        # http methods for both list and detail is the same
        url = self.product_list_url
        self.allowed_http_methods.check_allowed_methods(url, expected_methods=None)
    
    def test_product_url_resolves(self):
        url = self.product_list_url
        self.assertEqual(resolve(url).func.cls, ProductViewSet)
    
    def test_product_list_url(self):
        response = self.client.get(self.product_list_url)
        self.assertTrue(response.json().get('count') > 0)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_product_detail_url(self):                            
        response = self.client.get(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_comment_urls_http_methods(self):
        url = self.comment_list_url
        self.allowed_http_methods.check_allowed_methods(url, expected_methods=None)

    def test_comment_url_resolves(self):
        url = self.comment_list_url
        self.assertEqual(resolve(url).func.cls, CommentViewSet)
    
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
        self.auth_token = GenerateAuthToken().generate_auth_token(self.client)
        self.allowed_http_methods = AllowedHttpMethodTests(self)
        self.user = self.mock_objs.user_obj
        self.cart = self.mock_objs.cart_obj
        self.cartitems = self.mock_objs.cartitems_obj
        self.cart_list_url = reverse('cart-list')
        self.cart_detail_url = reverse('cart-detail', args=[self.cart.id])
        self.cartitems_list_url = self.cart_detail_url + 'items/'
        self.cartitems_detail_url = self.cart_detail_url + f'items/{self.cartitems.id}'

    def test_cart_urls_https_methods(self):
        pass

    def test_cart_url_resolves(self):
        pass

    def test_cart_list_url(self):
        self.api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {self.auth_token}'
        response = self.api_client.get(self.cart_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cart_detail_url(self):
        pass