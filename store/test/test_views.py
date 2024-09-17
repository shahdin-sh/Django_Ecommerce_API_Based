from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from rest_framework.reverse import reverse
from rest_framework import status


from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.utils import IntegrityError
from django.urls.exceptions import NoReverseMatch

from store.models import Product, Category, Comment, Cart, CartItem, Customer, Address
from store.serializers import (
    CartItemSerializer, 
    AddItemtoCartSerializer,
    ManagerAddressSerializer,
    ManagersAddAddressSerializer,
    AddAddressSerializer,
    AddressSerializer
)
from store.test.helpers.base_helper import MockObjects, UserAuthHelper, GenerateAuthToken

class ProductViewSetTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.user_auth_helper = UserAuthHelper()
        self.user_obj = self.mock_objs.user_obj
        self.product_obj = self.mock_objs.product_obj
        self.categoty_obj = self.mock_objs.category_obj
        self.product_list_url = reverse('product-list')
        self.product_detail_url = reverse('product-detail', args=[self.product_obj.slug])

        # different product objs, 4 in total
        self.product_1 = Product.objects.create(
            name = 'product1',
            category = self.categoty_obj,
            slug = 'product1',
            unit_price =  '90000',
            inventory = 10, 
        )
        self.product_2 = Product.objects.create(
            name = 'product2',
            category = self.categoty_obj,
            slug = 'product2',
            unit_price =  '50000',
            inventory = 4, 
        )
        self.product_3 = Product.objects.create(
            name = 'product3',
            category = self.categoty_obj,
            slug = 'product3',
            unit_price =  '20000',
            inventory = 1, 
        )

        self.product_manager_group = Group.objects.create(name='Product Manager')
    
    def set_authorization_header(self):
        self.user_auth_helper.set_authorization_header(self.api_client, self.auth_token)
    
    def set_manager_group(self):
        self.user_auth_helper.set_or_unset_manager_groups(True, self.user_obj, manager_group=self.product_manager_group)

    # Test Cases
    def test_product_objects_count(self):
        response = self.api_client.get(self.product_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)

    def test_create_product(self):
        self.set_authorization_header()
        self.set_manager_group()

        data = {
            'name': 'Product A',
            'unit_price': 100000,
            'inventory': 10,
            'category': f'http://testserver/store/categories/{self.categoty_obj.slug}/' 
        }

        response = self.api_client.post(self.product_list_url, data, 'json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
     
    def test_update_product(self):
        self.set_authorization_header()
        self.set_manager_group()

        data = {
            'name': 'updated name',
            'unit_price': 110000,
            'inventory': 10,
            'category': f'http://testserver/store/categories/{self.categoty_obj.slug}/' 
        }

        response = self.api_client.put(self.product_detail_url, data, 'json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_delete_product_under_protected_foreignkey(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.delete(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        error_msg = f'"product referenced through protected foreign key: {[orderitem for orderitem in self.product_obj.order_items.all()]}"'
        self.assertEqual(error_msg, response.content.decode('utf-8'))
    
    def test_delete_product_without_protected_foreignkey(self):
        self.set_authorization_header()
        self.set_manager_group()

        product_detail = reverse('product-detail', args=[self.product_1.slug])

        response = self.api_client.delete(product_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_product_valid_and_invlaid_lookup_field(self):
        response = self.api_client.get(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_product_detail = reverse('product-detail', args=[self.product_obj.id])
        response = self.api_client.get(invalid_product_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_product_default_queryset_ordering(self):
        response = self.api_client.get(self.product_list_url)
        results = [result['name'] for result in response.data['results']]
        self.assertEqual(results, ['product3','product2', 'product1', 'product'])

    def test_product_inventory_lte_filter(self):
        response = self.api_client.get(self.product_list_url, {'inventory_lte': 5})
        self.assertEqual(response.data['count'], 2)
    
    def test_product_inventory_gte_filter(self):
        response = self.api_client.get(self.product_list_url, {'inventory_gte': 3})
        self.assertEqual(response.data['count'], 3)
    
    def test_product_unit_price_lte_filter(self):
        response = self.api_client.get(self.product_list_url, {'min_price': 50000})
        self.assertEqual(response.data['count'], 2)
    
    def test_product_unit_price_gte_filter(self):
        response = self.api_client.get(self.product_list_url, {'max_price': 10000})
        self.assertEqual(response.data['count'], 4)
    
    def test_product_inventory_status_filter(self):
        critical_status_res = self.api_client.get(self.product_list_url, {'inventory_status': 'Critical'})
        self.assertEqual(critical_status_res.status_code, status.HTTP_200_OK)
        self.assertEqual(critical_status_res.data['count'], 4)

        medium_status_res = self.api_client.get(self.product_list_url, {'inventory_status': 'Medium'})
        # after order creation, product inventory will reduce | product_obj inventory != 7, = 10
        self.assertEqual(medium_status_res.data['count'], 1)

        good_status_res = self.api_client.get(self.product_list_url, {'inventory_status': 'Good'})
        self.assertEqual(good_status_res.data['count'], 0)
    
    def test_product_category_slug_filter(self):
        response = self.api_client.get(self.product_list_url, {'category__slug': 'category'})
        self.assertEqual(response.data['count'], 4)

    def test_product_search_by_name_filter(self):
        response = self.api_client.get(self.product_list_url, {'search': 'product1'})
        self.assertEqual(response.data['count'], 1)
    
    def test_product_search_by_category_filter(self):
        response = self.api_client.get(self.product_list_url, {'search': 'category'})
        self.assertEqual(response.data['count'], 4)

    def test_product_name_ordering_filter(self):
        ascending_order_response = self.api_client.get(self.product_list_url, {'ordering': 'name'})
        results = [result['name'] for result in ascending_order_response.data['results']]
        self.assertEqual(results, ['product','product1', 'product2', 'product3'])

        descending_order_response = self.api_client.get(self.product_list_url, {'ordering': '-name'})
        results = [result['name'] for result in descending_order_response.data['results']]
        self.assertEqual(results, ['product3', 'product2', 'product1', 'product'])
    
    def test_product_inventory_ordering_filter(self):
        ascending_order_response = self.api_client.get(self.product_list_url, {'ordering': 'inventory'})
        results = [result['name'] for result in ascending_order_response.data['results']]
        self.assertEqual(results, ['product3','product2', 'product', 'product1'])

        descending_order_response = self.api_client.get(self.product_list_url, {'ordering': '-inventory'})
        results = [result['name'] for result in descending_order_response.data['results']]
        self.assertEqual(results, ['product1', 'product', 'product2', 'product3'])
    
    def test_product_unit_price_ordering_filter(self):
        ascending_order_response = self.api_client.get(self.product_list_url, {'ordering': 'unit_price'})
        results = [result['name'] for result in ascending_order_response.data['results']]
        self.assertEqual(results, ['product3','product2', 'product1', 'product'])

        descending_order_response = self.api_client.get(self.product_list_url, {'ordering': '-unit_price'})
        results = [result['name'] for result in descending_order_response.data['results']]
        self.assertEqual(results, ['product', 'product1', 'product2', 'product3'])

    def test_product_pagination(self):
        response = self.api_client.get(self.product_list_url, {'page_size': 2, 'page': 1})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

        response = self.api_client.get(self.product_list_url, {'page_size': 2, 'page': 2})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['previous'])
        self.assertIsNone(response.data['next'])


class CategoryViewSetTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.user_auth_helper = UserAuthHelper()
        self.user_obj = self.mock_objs.user_obj
        self.product_obj = self.mock_objs.product_obj
        self.categoty_obj = self.mock_objs.category_obj
        self.category_list_url = reverse('category-list')
        self.category_detail_url = reverse('category-detail', args=[self.categoty_obj.slug])

        # different category objs, 3 in total
        self.category_1 = Category.objects.create(
            title = 'category1',
            slug = 'category1'
        )
        self.category_2 = Category.objects.create(
            title = 'category2',
            slug = 'category2'
        )
    
        self.product_manager_group = Group.objects.create(name='Product Manager')
    
    def set_authorization_header(self):
        self.user_auth_helper.set_authorization_header(self.api_client, self.auth_token)
    
    def set_manager_group(self):
        self.user_auth_helper.set_or_unset_manager_groups(True, self.user_obj, manager_group=self.product_manager_group)

    # Test Cases
    def test_category_objects_count(self):
        response = self.api_client.get(self.category_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)

    def test_create_category(self):
        self.set_authorization_header()
        self.set_manager_group()

        data = {'title': 'test category', 'slug': 'test-category'}

        response = self.api_client.post(self.category_list_url, data, 'json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
     
    def test_update_category(self):
        self.set_authorization_header()
        self.set_manager_group()

        data = {'title': 'some title for catgory'}

        response = self.api_client.put(self.category_detail_url, data, 'json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_delete_category_under_protected_foreignkey(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.delete(self.category_detail_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        error_msg = f'"category referenced through protected foreign key: {[product for product in self.categoty_obj.products.all()]}"'
        self.assertEqual(error_msg, response.content.decode('utf-8'))
    
    def test_delete_category_without_protected_foreignkey(self):
        self.set_authorization_header()
        self.set_manager_group()

        category_detail = reverse('category-detail', args=[self.category_1.slug])

        response = self.api_client.delete(category_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_category_valid_and_invlaid_lookup_field(self):
        response = self.api_client.get(self.category_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_category_detail = reverse('category-detail', args=[self.categoty_obj.id])
        response = self.api_client.get(invalid_category_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_cateogry_default_queryset_ordering(self):
        # set products for category_1
        self.product_test1 = Product.objects.create(
            name = 'product_test_1',
            category = self.category_1,
            slug = 'product-test-1',
            unit_price =  '50000',
            inventory = 4, 
        )
        self.product_test2 = Product.objects.create(
            name = 'product_test_2',
            category = self.category_1,
            slug = 'product_test_2',
            unit_price =  '20000',
            inventory = 1, 
        )

        response = self.api_client.get(self.category_list_url)
        results = [result['title'] for result in response.data['results']]
        self.assertEqual(results, ['category1', 'category', 'category2'])

        self.assertEqual(response.data['results'][0]['num_of_products'], 2)
    
    def test_category_filter_by_title(self):
        response = self.api_client.get(self.category_list_url, {'title': self.categoty_obj.title})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_category_pagination(self):
        response = self.api_client.get(self.category_list_url, {'page_size': 2, 'page': 1})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

        response = self.api_client.get(self.category_list_url, {'page_size': 2, 'page': 2})
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['previous'])
        self.assertIsNone(response.data['next'])


class CommentViewSetTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.factory = APIRequestFactory()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.user_auth_helper = UserAuthHelper()
        self.user_obj = self.mock_objs.user_obj
        self.product_obj = self.mock_objs.product_obj
        self.comment_obj = self.mock_objs.comment_obj
        self.comment_list_url = reverse('product-comments-list', kwargs={'product_slug':self.product_obj.slug})
        self.comment_detail_url = reverse(
            'product-comments-detail', 
            kwargs={
                'product_slug':self.product_obj.slug,
                'pk': self.comment_obj.pk
            }
        )
 
        # different comment objs, 4 in total
        self.comment_1 = Comment.objects.create(
            product = self.product_obj,
            name = 'comment1',
            body = 'random text for comment1',
            status = Comment.COMMENT_STATUS_APPROVED
        )
        self.comment_2 = Comment.objects.create(
            product = self.product_obj,
            name = 'comment2',
            body = 'random text for comment2',
            status = Comment.COMMENT_STATUS_APPROVED
        )
        self.comment_3 = Comment.objects.create(
            product = self.product_obj,
            name = 'comment3',
            body = 'random text for comment3',
            status = Comment.COMMENT_STATUS_NOT_APPROVED
        )
    
        self.content_manager_group = Group.objects.create(name='Content Manager')
    
    def set_authorization_header(self):
        self.user_auth_helper.set_authorization_header(self.api_client, self.auth_token)
    
    def set_manager_group(self):
        self.user_auth_helper.set_or_unset_manager_groups(True, self.user_obj, manager_group=self.content_manager_group)
    
    # Test Cases
    def test_comment_objects_count(self):
        response = self.api_client.get(self.comment_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
    
    def test_create_comment(self):
        self.set_authorization_header()
        self.set_manager_group()

        data = {
            'name' : 'test comment',
            'body' : 'random text for test comment',
            'status' : Comment.COMMENT_STATUS_APPROVED
        }

        response = self.api_client.post(self.comment_list_url, data, 'json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
     
    def test_update_comment(self):
        self.set_authorization_header()
        self.set_manager_group()

        data = {
            'name': 'test comment',
            'body' : 'change text for test comment',
        }

        response = self.api_client.put(self.comment_detail_url, data, 'json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_delete_commment(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.delete(self.comment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_comment_valid_and_invalid_lookup_field(self):
        response = self.api_client.get(self.comment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_comment_detail = reverse(
            'product-comments-detail', 
            kwargs={
                'product_slug':self.product_obj.slug,
                'pk': 100
            }
        )
        response = self.api_client.get(invalid_comment_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_comment_valid_and_invalid_product_slug(self):
        response = self.api_client.get(self.comment_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_comment_kwargs = reverse(
            'product-comments-detail', 
            kwargs={
                'product_slug':'invalid product slug',
                'pk': self.comment_obj.pk
            }
        )
        response = self.api_client.get(invalid_comment_kwargs)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_comment_default_querysey_ordering(self):
        response = self.api_client.get(self.comment_list_url)
        results = [result['name'] for result in response.data['results']]
        self.assertEqual(results, ['comment2', 'comment1', 'comment'])
    
    def test_comment_serializer_context(self):
        pass

    def test_comment_with_different_status(self):
        response = self.api_client.get(self.comment_list_url)
        results = [result['name'] for result in response.data['results']]

        approved_comments = [self.comment_2, self.comment_1, self.comment_obj]
        [self.assertIn(comment.name, results) for comment in approved_comments]
        [self.assertTrue(comment.status == Comment.COMMENT_STATUS_APPROVED) for comment in approved_comments]

        self.assertNotIn('comment3', results)
        self.assertTrue(self.comment_3.status == Comment.COMMENT_STATUS_NOT_APPROVED)

    def test_comment_name_ordering_filter(self):
        ascending_response = self.api_client.get(self.comment_list_url, {'ordering': 'name'})
        results = [result['name'] for result in ascending_response.data['results']]
        self.assertEqual(results, ['comment', 'comment1', 'comment2'])

        descending_response = self.api_client.get(self.comment_list_url, {'ordering': '-name'})
        results = [result['name'] for result in descending_response.data['results']]
        self.assertEqual(results, ['comment2', 'comment1', 'comment'])
    
    def test_comment_datetime_created_ordering_filter(self):
        ascending_response = self.api_client.get(self.comment_list_url, {'ordering': 'datetime_created'})
        results = [result['name'] for result in ascending_response.data['results']]
        self.assertEqual(results, ['comment', 'comment1', 'comment2'])

        descending_response = self.api_client.get(self.comment_list_url, {'ordering': '-datetime_created'})
        results = [result['name'] for result in descending_response.data['results']]
        self.assertEqual(results, ['comment2', 'comment1', 'comment'])
    
    def test_comment_pagination(self):
        response = self.api_client.get(self.comment_list_url, {'page_size': 2, 'page': 1})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

        response = self.api_client.get(self.comment_list_url, {'page_size': 2, 'page': 2})
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['previous'])
        self.assertIsNone(response.data['next'])


class CartViewSetTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.user_auth_helper = UserAuthHelper()
        self.user_obj = self.mock_objs.user_obj
        self.cart_obj = self.mock_objs.cart_obj
        self.cart_list_url = reverse('cart-list')
        self.cart_detail_url = reverse('cart-detail', args=[self.cart_obj.id])

        # different cart objs, 4 in total
        self.cart_1 = Cart.objects.create(
            id = 'b3f8e7c9-6bda-42ad-93ab-3c091fe7a581',
        )
        self.cart_2 = Cart.objects.create(
            id = 'f5ac1e23-4cbe-45a7-b2a2-3e081df2b971',
        )
        self.cart_3 = Cart.objects.create(
            id = 'd4e7b8f2-9cfa-4829-a8f1-5d210af3c874',
        )
    
    def set_authorization_header(self):
        self.user_auth_helper.set_authorization_header(self.api_client, self.auth_token)
     
    # Test Cases
    def test_cart_objects_count(self):
        self.set_authorization_header()

        response = self.api_client.get(self.cart_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)
    
    def test_cart_create(self):
        self.set_authorization_header()

        response = self.api_client.post(self.cart_list_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_cart_update(self):
        self.set_authorization_header()

        response = self.api_client.put(self.cart_detail_url)

        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_cart_delete(self):
        # testing with more detail of different users access in test_endpoints.py 
        self.set_authorization_header()

        response = self.api_client.delete(self.cart_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cart_valid_and_invalid_lookup_field(self):
        self.set_authorization_header()

        response = self.api_client.get(self.cart_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_cart_detail = reverse('cart-detail', args=['q5ac1e23-4cbe-45a7-b2a2-3e081df2b971'])
        response = self.api_client.get(invalid_cart_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_cart_default_queryset_ordering(self):
        self.set_authorization_header()

        response = self.api_client.get(self.cart_list_url)
        results = [result['id'] for result in response.data['results']]
        self.assertEqual(results, [self.cart_3.id, self.cart_2.id, self.cart_1.id, self.cart_obj.id])
    
    def test_cart_pagination(self):
        self.set_authorization_header()

        response = self.api_client.get(self.cart_list_url, {'page_size': 2, 'page': 1})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

        response = self.api_client.get(self.cart_list_url, {'page_size': 2, 'page': 2})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['previous'])
        self.assertIsNone(response.data['next'])
    
    def test_valid_cart_lookup_value_regax(self):
        self.set_authorization_header()
        correct_uuid = 'a5ac1e23-4cbe-45a7-b2a2-3e081df2b971'
        test_cart = Cart.objects.create(id=correct_uuid)

        response = self.api_client.get((reverse('cart-detail', args=[test_cart.id])))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valid_cart_lookup_value_regax(self):
        invalid_cart_ids = [
            'a2dbc6-a627bc416585202d151fe8b357',
            '12345-abc',
            'a2dbc6a6-27bc-4165',
            'a2brwplfi-rtew-qwer-rfvg-poiq12mfekw'
        ]

        for invalid_cart_ids in invalid_cart_ids:
            with self.assertRaises(NoReverseMatch) as context:
                (reverse('cart-detail', args=[invalid_cart_ids]))

            self.assertIn(invalid_cart_ids, str(context.exception))


class CartItemViewSetTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.user_auth_helper = UserAuthHelper()
        self.user_obj = self.mock_objs.user_obj
        self.cart_obj = self.mock_objs.cart_obj
        self.product_obj = self.mock_objs.product_obj
        self.cartitems_obj = self.mock_objs.cartitems_obj
        self.cartitems_list_url = reverse('cart-items-list', kwargs={'cart_id': self.cart_obj.id})
        self.cartitems_detail_url = reverse('cart-items-detail', 
            kwargs = {
                'cart_id': self.cart_obj.id,
                'pk': self.cartitems_obj.id
            }
        )
        
        # different cartitems objs, 4 in total
        self.cartitems_1 = CartItem.objects.create(
            cart = self.cart_obj,
            product = Product.objects.create(
                name = 'product_item1',
                category = self.mock_objs.category_obj,
                slug = 'product-item1',
                unit_price =  '10000',
                inventory = 7, 
            ),
            quantity = 6
        )
        self.cartitems_2 = CartItem.objects.create(
            cart = self.cart_obj,
            product = Product.objects.create(
                name = 'product_item2',
                category = self.mock_objs.category_obj,
                slug = 'product-item2',
                unit_price =  '20000',
                inventory = 5, 
            ),
            quantity = 4
        )
        self.cartitems_3 = CartItem.objects.create(
            cart = self.cart_obj,
            product = Product.objects.create(
                name = 'product_item3',
                category = self.mock_objs.category_obj,
                slug = 'product-item3',
                unit_price =  '10000',
                inventory = 2, 
            ),
            quantity = 1
        )
    
    def set_authorization_header(self):
        self.user_auth_helper.set_authorization_header(self.api_client, self.auth_token)
     
    # Test Cases
    def test_cartitem_objects_count(self):
        self.set_authorization_header()

        response = self.api_client.get(self.cartitems_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)
    
    def test_cartitem_create(self):
        self.set_authorization_header()

        test_product = Product.objects.create(
            name = 'test product',
            category = self.mock_objs.category_obj,
            slug = 'test-product',
            unit_price =  '10000',
            inventory = 20, 
        )

        data = {
            'product': test_product.id,
            'quantity': 5
        }

        response = self.api_client.post(self.cartitems_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # check product stock after creation
        product_stock_after_creation = test_product.inventory - data['quantity']
        self.assertEqual(response.data['current_product_stock'], product_stock_after_creation)
    
    def test_cartitem_create_with_in_usage_product(self):
        self.set_authorization_header()

        # use in creating self.cartitem_obj
        in_used_product = self.product_obj

        data = {
            'product': in_used_product.id,
            'quantity': 4
        }
        
        with self.assertRaises(IntegrityError) as context:
            self.api_client.post(self.cartitems_list_url, data)
        
        self.assertIn((f'{self.cart_obj.id}, {self.product_obj.id}'), str(context.exception))
    
    def test_cartitem_create_quantity_input_validation(self):
        self.set_authorization_header()

        self.assertTrue(self.product_obj.inventory == 7)

        test_data = [
            {'quantity': 8, 'error_msg': f'["quantity must be less than {self.product_obj.name} inventory"]'},
            {'quantity': 0, 'error_msg': '["quantity must be greater or equal to 1"]'}
        ]

        for data in test_data:
            response = self.api_client.put(self.cartitems_detail_url, {'quantity': data['quantity']})
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertEqual(data['error_msg'], response.content.decode('utf-8'))
    
    def test_cartitem_update(self):
        self.set_authorization_header()

        data = {'quantity': 1}

        response = self.api_client.put(self.cartitems_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cartitem_delete(self):
        # testing with more detail of different users access in test_endpoints.py 
        self.set_authorization_header()

        response = self.api_client.delete(self.cartitems_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_cartitem_valid_and_invalid_lookup_field(self):
        self.set_authorization_header()

        response = self.api_client.get(self.cartitems_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.assertRaises(NoReverseMatch):
            reverse('cart-items-detail', kwargs={'cart_id': self.cart_obj, 'pk': 100})
    
    def test_cartitem_valid_and_invalid_cart_id(self):
        self.set_authorization_header()

        response = self.api_client.get(self.cartitems_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.assertRaises(NoReverseMatch):
            reverse('cart-items-detail', kwargs={'cart_id': 100, 'pk': self.cartitems_obj})
    
    def test_cartitem_default_queryset_ordering(self):
        self.set_authorization_header()

        response = self.api_client.get(self.cartitems_list_url)
        results = [result['id'] for result in response.data]
        self.assertEqual(results, [self.cartitems_obj.id, self.cartitems_1.id, self.cartitems_2.id, self.cartitems_3.id])
    
    def test_cartitem_get_serializer_class(self):
        self.set_authorization_header()

        serializer_class_data  = [
            {'response': self.api_client.post(self.cartitems_list_url), 'serializer_class': AddItemtoCartSerializer},
            {'response': self.api_client.get(self.cartitems_list_url), 'serializer_class': CartItemSerializer}
        ]

        for data in serializer_class_data:
            view = data['response'].wsgi_request.resolver_match.func.cls()
            view.request = data['response'].wsgi_request

            self.assertEqual(view.get_serializer_class(), data['serializer_class'])

    def test_cartitem_pagination(self):
        self.set_authorization_header()

        response = self.api_client.get(self.cartitems_list_url, {'page_size': 2})

        respones_data = response.json()

        self.assertNotIn('next', respones_data)
        self.assertNotIn('previous', respones_data)
        self.assertNotIn('count', respones_data)
        self.assertNotEqual(len(respones_data), 2)

        # check that response is a list and not a paginated structure
        self.assertIsInstance(respones_data, list)


class CustomerViewSetTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.user_auth_helper = UserAuthHelper()
        self.user_obj = self.mock_objs.user_obj
        self.customer_obj = self.mock_objs.customer_obj
        self.customer_list_url = reverse('customer-list')
        self.customer_detail_url = reverse('customer-detail', args=[self.customer_obj.id])
        self.customer_me_action_url = reverse('customer-list') + 'me/'

        # different customer objs, 4 in total
        self.user_1 = get_user_model().objects.create_user(
            username = 'username1',
            email = 'username1@gmail.com',
            password = 'user1',
        )
        self.user_2 = get_user_model().objects.create_user(
            username = 'username2',
            email = 'username2@gmail.com',
            password = 'user1',
        )
        self.user_3 = get_user_model().objects.create_user(
            username = 'username3',
            email = 'username3@gmail.com',
            password = 'user1',
        )
        self.customer_1 = Customer.objects.get(user__username='username1')
        self.customer_2 = Customer.objects.get(user__username='username2')
        self.customer_3 = Customer.objects.get(user__username='username3')
    
        self.customer_manager_group = Group.objects.create(name='Customer Manager')
    
    def set_authorization_header(self):
        self.user_auth_helper.set_authorization_header(self.api_client, self.auth_token)
    
    def set_manager_group(self):
        self.user_auth_helper.set_or_unset_manager_groups(True, self.user_obj, manager_group=self.customer_manager_group)
    
    # Test Cases
    def test_customer_objs_count(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.get(self.customer_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)

    def test_customer_create(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.post(self.customer_list_url, {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_customer_create_through_user(self):
        self.set_authorization_header()
        self.set_manager_group()

        test_user = get_user_model().objects.create_user(
            username = 'test_user',
            email = 'testuser@gmail.com',
            password = 'usertest',
        )

        response = self.api_client.get(self.customer_list_url, {'search': test_user.username})
        self.assertEqual(response.data['count'], 1)

    def test_customer_update(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.put(self.customer_detail_url, {'birth_date': '2022-06-15'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.api_client.get(self.customer_detail_url).data['birth_date'], '2022-06-15')

    def test_customer_delete(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.delete(self.customer_list_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_customer_valid_and_invalid_lookup_field(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.get(self.customer_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_customer_detail = reverse('customer-detail', args=[100])
        response = self.api_client.get(invalid_customer_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_customer_default_queryset_ordering(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.get(self.customer_list_url)
        results = [result['id'] for result in response.data['results']]
        self.assertEqual(results, [self.customer_obj.id, self.customer_1.id, self.customer_2.id, self.customer_3.id])

    def test_customer_with_no_address_filter(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.get(self.customer_list_url, {'no_address': True})
        results = [result['id'] for result in response.data['results']]
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(results, [self.customer_1.id, self.customer_2.id, self.customer_3.id])
        self.assertNotIn(self.customer_obj.id, results)
    
    def test_customer_with_address_filter(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.get(self.customer_list_url, {'no_address': False})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.customer_obj.id)
    
    def test_customer_search_by_username_filter(self):
        self.set_authorization_header()
        self.set_manager_group()

        for user in [self.user_1, self.user_2, self.user_3]:
            url = self.customer_list_url + f'?search={user.username}'
            response = self.api_client.get(url)
            self.assertEqual(response.data['count'], 1)
            self.assertEqual(response.data['results'][0]['user'], user.username)
        
    def test_customer_pagination(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.get(self.customer_list_url, {'page_size': 2, 'page':1})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

        response = self.api_client.get(self.customer_list_url, {'page_size': 2, 'page': 2})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['previous'])
        self.assertIsNone(response.data['next'])

    def test_customer_me_action_get(self):
        self.set_authorization_header()

        response = self.api_client.get(self.customer_me_action_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('birth_date', response.data)
        self.assertIn('address', response.data)
        self.assertIn('address', response.data)
    
    def test_customer_me_action_update(self):
        self.set_authorization_header()

        response = self.api_client.put(self.customer_me_action_url, {'birth_date': '2015-06-15'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.api_client.get(self.customer_me_action_url).data['birth_date'], '2015-06-15')
    
    def test_customer_me_action_delete(self):
        self.set_authorization_header()

        response = self.api_client.delete(self.customer_me_action_url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_customer_me_action_detail(self):
        self.set_authorization_header()

        customer_me_detail = reverse('customer-list') + f'me/{10}'
        response = self.api_client.get(customer_me_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AddressViewSetTests(APITestCase):
    def setUp(self):
        self.api_client = APIClient()
        self.mock_objs = MockObjects()
        self.auth_token = GenerateAuthToken().generate_auth_token()
        self.user_auth_helper = UserAuthHelper()
        self.user_obj = self.mock_objs.user_obj
        self.customer_obj = self.mock_objs.customer_obj
        self.address_obj = self.mock_objs.address_obj
        self.address_list_url = reverse('address-list')
        self.address_detail_url = reverse('address-detail', args=[self.address_obj.pk])

        self.user_a = get_user_model().objects.create_user(
            username = 'usernamea',
            email = 'usernamea@gmail.com',
            password = 'user1',
        )
        self.user_b = get_user_model().objects.create_user(
            username = 'usernameb',
            email = 'usernameb@gmail.com',
            password = 'user2',
        )
        self.user_c = get_user_model().objects.create_user(
            username = 'usernamec',
            email = 'usernamec@gmail.com',
            password = 'user3',
        )

        # different address objs, 4 in total
        self.address_1 = Address.objects.create(
            customer = Customer.objects.get(user=self.user_a),
            province = 'province 1',
            city = 'city 1',
            street = 'street number 1'
        )
        self.address_2 = Address.objects.create(
            customer = Customer.objects.get(user=self.user_b),
            province = 'province 2',
            city = 'city 2',
            street = 'street number 2'
        )
        self.address_3 = Address.objects.create(
            customer = Customer.objects.get(user=self.user_c),
            province = 'province 3',
            city = 'city 3',
            street = 'street number 3'
        )
        # error from creating the same user as upper class, lead to unique constraints, but why?

        self.customer_manager_group = Group.objects.create(name='Customer Manager')
    
    def set_authorization_header(self):
        self.user_auth_helper.set_authorization_header(self.api_client, self.auth_token)
    
    def set_manager_group(self):
        self.user_auth_helper.set_or_unset_manager_groups(True, self.user_obj, manager_group=self.customer_manager_group)
    
    # Test Cases
    def test_address_objs_count_for_managers_and_users(self):
        self.set_authorization_header()

        response = self.api_client.get(self.address_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

        self.set_manager_group()
        response = self.api_client.get(self.address_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 4)

    def test_address_create_for_managers(self):
        self.set_authorization_header()
        self.set_manager_group()

        test_customer = Customer.objects.get(
            user = get_user_model().objects.create(
                username='test user',
                email='testuser@gmail.com',
                password='testpass123'
            )
        )

        data = {
            'customer': test_customer.id,
            'province': 'test province',
            'city': 'test city',
            'street': 'test street'
        }
        
        post_response = self.api_client.post(self.address_list_url, data)
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)

        address_pk = Address.objects.get(customer=test_customer).pk
        expected_data = {
            'pk': address_pk,
            'user': 'test user',
            'detail': f'http://testserver/store/addresses/{address_pk}/',
            'customer':  f'http://testserver/store/customers/{test_customer.id}/',
            'province': data['province'],
            'city': data['city'],
            'street': data['street']
        }

        get_response = self.api_client.get(self.address_list_url, {'search': 'test user'})
        self.assertDictEqual(get_response.data['results'][0], expected_data)

    def test_address_create_for_customers_already_with_address_for_managers(self):
        self.set_authorization_header()
        self.set_manager_group()

        data = {
            'customer': self.customer_obj.id,
            'city': "test city",
            'province': "test province",
            'street': "test street",
        }

        response = self.api_client.post(self.address_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # manager address serializer will remove customers that already has address from the customer field
        self.assertEqual(
            response.json(), 
            {'customer': [f'Invalid pk "{self.customer_obj.id}" - object does not exist.']}
        ) 
    
    def test_address_create_for_users(self):
        self.set_authorization_header()

        Address.objects.get(customer=self.customer_obj).delete()

        data = {
            'city': "test city",
            'province': "test province",
            'street': "test street"
        }

        post_response = self.api_client.post(self.address_list_url, data)
        self.assertEqual(post_response.status_code, status.HTTP_200_OK)

        address_pk = Address.objects.get(customer=self.customer_obj).pk
        expected_data = [{
            "province": data['province'],
            "city": data['city'],
            "street": data['street'],
            "detail": f"http://testserver/store/addresses/{address_pk}/"
        }]

        get_response = self.api_client.get(self.address_list_url, {'search': 'username'})
        self.assertEqual(get_response.json(), expected_data)
    
    
    def test_address_create_for_customers_already_with_address_for_users(self):
        self.set_authorization_header()

        data = {
            'city': "test city",
            'province': "test province",
            'street': "test street"
        }

        response = self.api_client.post(self.address_list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(),  {'non_field_errors': ['address has already created.']})
    
    def test_address_create_request_via_serializer_context_for_users(self):
        auth_token = GenerateAuthToken().generate_auth_token(
            username='usernamea', 
            password='user1'
        )
        self.user_auth_helper.set_authorization_header(self.api_client, auth_token)

        data = {
            'city': "test city",
            'province': "test province",
            'street': "test street"
        }

        response = self.api_client.post(self.address_list_url, data)
        view = response.wsgi_request.resolver_match.func.cls()
        view.request = response.wsgi_request
        view.format_kwarg = None
        serializer = view.get_serializer()
        
        self.assertIn('request', serializer.context)
        self.assertEqual(serializer.context['request'].user, self.user_a)

    def test_address_update_for_manager(self):
        self.set_authorization_header()
        self.set_manager_group()

        data = {
            'province': 'canada',
            'city': 'torento',
            'street': self.address_3.street
        }

        address_detail = reverse('address-detail', args=[self.address_3.pk])
        response = self.api_client.put(address_detail, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        [self.assertIn(data[key], response.data[key]) for key in data]
    
    def test_address_update_for_user(self):
        self.set_authorization_header()

        data = {
            'province': 'canada',
            'city': 'torento',
            'street': self.address_obj.street
        }

        user_address = self.address_detail_url
        response = self.api_client.put(user_address, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        [self.assertIn(data[key], response.data[key]) for key in data]
    
    def test_address_delete_for_managers(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.delete(self.address_detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
    
    def test_address_delete_for_users(self):
        self.set_authorization_header()

        response = self.api_client.delete(self.address_detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_address_valid_and_invalid_lookup_field(self):
        self.set_authorization_header()

        response = self.api_client.get(self.address_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        invalid_address_detail = reverse('address-detail', args=[self.address_1.pk])
        response = self.api_client.get(invalid_address_detail)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('No Address matches the given query.', response.content.decode('utf-8'))

    def test_address_default_queryset_ordering_for_managers(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.get(self.address_list_url)
        results = [result['pk'] for result in response.data['results']]
        self.assertEqual(results, [self.address_obj.pk, self.address_1.pk, self.address_2.pk, self.address_3.pk])

    def test_address_get_serializer_class_for_managers(self):
        self.set_authorization_header()
        self.set_manager_group()

        serializer_class_data  = [
            {'response': self.api_client.get(self.address_list_url), 'serializer_class': ManagerAddressSerializer},
            {'response': self.api_client.post(self.address_list_url), 'serializer_class': ManagersAddAddressSerializer},
            {'response': self.api_client.put(self.address_detail_url), 'serializer_class': AddressSerializer}
        ]

        for data in serializer_class_data:
            view = data['response'].wsgi_request.resolver_match.func.cls()
            view.request = data['response'].wsgi_request

            self.assertEqual(view.get_serializer_class(), data['serializer_class'])
    
    def test_address_get_serializer_class_for_users(self):
        self.set_authorization_header()

        serializer_class_data  = [
            {'response': self.api_client.get(self.address_list_url), 'serializer_class': AddressSerializer},
            {'response': self.api_client.post(self.address_list_url), 'serializer_class': AddAddressSerializer},
            {'response': self.api_client.put(self.address_detail_url), 'serializer_class': AddressSerializer}
        ]

        for data in serializer_class_data:
            view = data['response'].wsgi_request.resolver_match.func.cls()
            view.request = data['response'].wsgi_request

            self.assertEqual(view.get_serializer_class(), data['serializer_class'])

    def test_address_search_by_customer_user_username_filter(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.get(self.address_list_url, {'search': self.address_1.customer.user.username})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['pk'], self.address_1.pk)

    def test_address_pagination_for_managers(self):
        self.set_authorization_header()
        self.set_manager_group()

        response = self.api_client.get(self.address_list_url, {'page': '1', 'page_size': '2'})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])

        response = self.api_client.get(self.address_list_url, {'page': '2', 'page_size': '2'})
        self.assertEqual(len(response.data['results']), 2)
        self.assertIsNone(response.data['next'])
        self.assertIsNotNone(response.data['previous'])

    def test_address_pagination_for_users(self):
        self.set_authorization_header()

        response = self.api_client.get(self.address_list_url, {'page': '1', 'page_size': 1})

        respones_data = response.json()

        self.assertNotIn('next', respones_data)
        self.assertNotIn('previous', respones_data)
        self.assertNotIn('count', respones_data)
        self.assertNotEqual(len(respones_data), 2)

        # check that response is a list and not a paginated structure
        self.assertIsInstance(respones_data, list)

