from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from django.urls import resolve
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from ..views import CategoryViewSet, ProductViewSet, CommentViewSet
from ..models import Product, Category, Comment

User = get_user_model()

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
        self.allowed_http_methods = AllowedHttpMethodTests(self)
        self.category = Category.objects.create(
            title = 'category',
            slug = 'category'
        )
        self.product = Product.objects.create(
            name = 'product',
            category = self.category,
            slug = 'product',
            unit_price =  '100000',
            inventory = 10, 
        )
        self.comment = Comment.objects.create(
            product = self.product,
            name = 'comment',
            body = 'random text for comment',
            status = Comment.COMMENT_STATUS_APPROVED
        )
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

    def test_category_url_http_methods(self):
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
    
    def test_product_url_http_methods(self):
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
    
    def test_comment_url_http_methods(self):
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
    