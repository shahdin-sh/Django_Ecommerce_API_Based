from rest_framework.test import APITestCase, APIClient, APIRequestFactory
from rest_framework.reverse import reverse
from rest_framework import status


from django.contrib.auth.models import Group

from store.models import Product, Category, Comment
from store.test.helpers.base_helper import MockObjects, UserAuthHelper, GenerateAuthToken
from store.views import CommentViewSet

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

    def test_product_search_by_name(self):
        response = self.api_client.get(self.product_list_url, {'search': 'product1'})
        self.assertEqual(response.data['count'], 1)
    
    def test_product_search_by_category(self):
        response = self.api_client.get(self.product_list_url, {'search': 'category'})
        self.assertEqual(response.data['count'], 4)
    
    def test_product_default_queryset_ordering_filter(self):
        response = self.api_client.get(self.product_list_url)
        results = [result['name'] for result in response.data['results']]
        self.assertEqual(results, ['product3','product2', 'product1', 'product'])

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
    
    def test_comment_default_querysey_filtering(self):
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


    



    




