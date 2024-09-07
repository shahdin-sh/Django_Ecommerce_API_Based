import logging

from rest_framework.test import APIClient
from django.urls import resolve

from store.test.helpers.base_helper import UserAuthHelper
from store.test.helpers.expected_status_codes import EXPECTED_STATUS_CODES


class ApiEndpointsAccessHelper():
    def __init__(self, test_case):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('test_status')


        self.test_case = test_case
        self.api_client = APIClient()
        self.user_auth_helper = UserAuthHelper()
        
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

                self.logger.info(test_log)

            except AssertionError:
                error_log = f'{method} Method in {access} access | ex_sc:{response.status_code} | sc:{status_code} | content:{response.content}'

                self.logger.error(error_log)
                raise AssertionError(error_log)
    
    def urls_method_access_test(self, url:str, name:str, auth_token, user, manager_group:None):
        access_level = [
            ('anon', lambda: self.user_auth_helper.unset_authorization_header(self.api_client)),
            ('user', lambda: self.user_auth_helper.set_authorization_header(self.api_client, auth_token)),
            ('manager', lambda: self.user_auth_helper.set_or_unset_manager_groups(set_group=True, user=user, manager_group=manager_group)),
            ('admin', lambda: self.user_auth_helper.set_to_superuser(set_superuser=True, user=user))
        ]

        for access, config_access in access_level:
            if access == 'manager' and manager_group is None:
                continue
        
            # Always reset user access config at the first of the loop
            if access == 'anon' or access == 'user':
                self.user_auth_helper.set_or_unset_manager_groups(set_group=False, user=user, manager_group=manager_group)
                self.user_auth_helper.set_to_superuser(set_superuser=False, user=user)

            config_access()

            self.get_expected_status_codes(url, EXPECTED_STATUS_CODES[access][name], access)