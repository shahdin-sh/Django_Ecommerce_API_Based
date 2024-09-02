import logging

from rest_framework.test import APIClient
from rest_framework import status

from django.urls import resolve
from django.contrib.auth.models import Group

from .base_helper import BaseHelper
from .expected_status_codes import EXPECTED_STATUS_CODES
from ...models import Product, Category

class ApiEndpointsAccessHelper():
    def __init__(self, test_case):
        self.test_case = test_case
        self.api_client = APIClient()
        self.base_helper = BaseHelper()
        #  # Set up logging configuration
        # self.logger = logging.getLogger(__name__)
        # self.logger.setLevel(logging.DEBUG)  # You can set this to INFO or ERROR as needed
        
        # # Create a console handler and set level to debug
        # handler = logging.StreamHandler()
        # handler.setLevel(logging.DEBUG)
        
        # # Create a formatter and set it for the handler
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # handler.setFormatter(formatter)
        
        # # Add the handler to the logger
        # self.logger.addHandler(handler)

    
    def get_expected_status_codes(self, url:str, expected_status_codes:dict, access:str):
        http_methods = {
            'OPTIONS': self.api_client.options,
            'GET': self.api_client.get,
            'POST': self.api_client.post,
            'PUT': self.api_client.put,
            'PATCH': self.api_client.patch,
            'DELETE': self.api_client.delete,
        }

        if 'list' in resolve(url).url_name:
            for method in ['PUT', 'PATCH', 'DELETE']:
                expected_status_codes.pop(method, None)
        else:
            expected_status_codes.pop('POST', None)
           
        for method, status_code in expected_status_codes.items():
            response = http_methods[method](url)
            try:
                self.test_case.assertEqual(response.status_code, status_code)
                test_log = f'pass | url:{url} | method:{method} | ex_sc:{status_code} | sc:{response.status_code} | {access} access'

                print(test_log)

            except AssertionError:
                raise AssertionError(f'{method} Method in {access} access | ex_sc:{response.status_code} | sc:{status_code} | content:{response.content}')
    
    def urls_method_access_test(self, url:str, name:str, auth_token, user, manager_group:None):
        access_level = [
            ('anon', lambda: self.base_helper.unset_authorization_header(self.api_client)),
            ('user', lambda: self.base_helper.set_authorization_header(self.api_client, auth_token)),
            ('manager', lambda: self.base_helper.set_or_unset_manager_groups(set_group=True, user=user, manager_group=manager_group)),
            ('admin', lambda: self.base_helper.set_to_superuser(set_superuser=True, user=user))
        ]

        for access, config_access in access_level:
            if access == 'manager' and manager_group is None:
                continue
        
            # Always reset user access before configuring access
            self.base_helper.set_or_unset_manager_groups(set_group=False, user=user, manager_group=manager_group)
            self.base_helper.set_to_superuser(set_superuser=False, user=user)

            config_access()

            self.get_expected_status_codes(url, EXPECTED_STATUS_CODES[access][name], access)