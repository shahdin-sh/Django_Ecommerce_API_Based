from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient

from django.contrib.auth.models import Group
from django.urls import resolve

from store.test.helpers.base_helper import MockObjects, GenerateAuthToken
from store.test.helpers.endpoints_access_helper import ApiEndpointsAccessHelper

from store.views import (
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


class ProductUrlsTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()  
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.endpoint_acess_helper = ApiEndpointsAccessHelper(self)
        self.user = self.mock_objs.user_obj
        self.category = self.mock_objs.category_obj
        self.product = self.mock_objs.product_obj
        self.comment = self.mock_objs.comment_obj
        self.category_list_url = reverse('category-list')
        self.category_detail_url = reverse('category-detail', args=[self.category.slug])
        self.product_list_url = reverse('product-list')
        self.product_detail_url = reverse('product-detail', args=[self.product.slug])
        self.comment_list_url = reverse('product-comments-list', kwargs={'product_slug':self.product.slug})
        self.comment_detail_url =  reverse(
            'product-comments-detail', 
            kwargs={
                'product_slug':self.product.slug,
                'pk': self.comment.pk
            }
        )

        #  Create a user group to ensure throttling and permissions are correctly applied in tests. 
        #  The test environment mirrors the actual conditions under which the URL paths are accessed.
        self.product_manager_group = Group.objects.create(name='Product Manager')
        self.comment_manager_group = Group.objects.create(name='Content Manager')

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
        self.mock_objs = MockObjects() # Instantiate MockObjects
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.endpoint_acess_helper = ApiEndpointsAccessHelper(self)
        self.user = self.mock_objs.user_obj
        self.cart = self.mock_objs.cart_obj
        self.cartitems = self.mock_objs.cartitems_obj
        self.cart_list_url = reverse('cart-list')
        self.cart_detail_url = reverse('cart-detail', args=[self.cart.id])
        self.cartitems_list_url = self.cart_detail_url + 'items/'
        self.cartitems_detail_url = self.cart_detail_url + f'items/{self.cartitems.id}/'
    
    # Test Methods
    def test_cart_urls_resolves(self):
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

    def test_cartitems_urls_resolves(self):
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
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
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
   
    def test_customer_info_url_resolves(self):
        self.assertEqual(resolve(self.customer_info_url).func.cls, CustomerViewSet)

    def test_customer_info_url_access(self):
        url = self.customer_info_url
        self.endpoint_acess_helper.urls_method_access_test(url, 'customer_info', 
            self.auth_token, self.user, self.customer_manager_group
        )
    
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
        self.endpoint_acess_helper = ApiEndpointsAccessHelper(self)
        self.user = self.mock_objs.user_obj
        self.order = self.mock_objs.order_obj
        self.orderitems = self.mock_objs.orderitems_obj
        self.order_list_url = reverse('order-list')
        self.order_detail_url = reverse('order-detail', args=[self.order.id])

        self.order_manager_group = Group.objects.create(name='Order Manager')
    
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
        self.endpoint_acess_helper = ApiEndpointsAccessHelper(self)
        self.user = self.mock_objs.user_obj
        self.payment_url = reverse('payment-process')
    
    # Test Methods           
    def test_payment_url_resolves(self):
        self.assertEqual(resolve(self.payment_url).func.cls, PaymentProcess)
    
    def test_payment_urls_access(self):
        url = self.payment_url
        self.endpoint_acess_helper.urls_method_access_test(self.payment_url, 'payment', 
            self.auth_token, self.user, manager_group=None
        )