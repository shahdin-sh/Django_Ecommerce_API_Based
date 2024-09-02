from rest_framework.test import APIClient

from django.contrib.auth.models import Group
from django.contrib.auth.models import User


class BaseHelper():
    def set_or_unset_manager_groups(self, set_group:bool, user:User, manager_group:Group):
        if set_group:
            user.groups.set([manager_group])
        else:
            user.groups.remove(manager_group)
    
    def set_authorization_header(self, api_client:APIClient , auth_token):
        api_client.defaults['HTTP_AUTHORIZATION'] = f'JWT {auth_token}'
    
    def unset_authorization_header(self, api_client:APIClient):
        api_client.defaults.pop('HTTP_AUTHORIZATION', None)

    def set_to_superuser(self, set_superuser:bool, user:object):
        if set_superuser:
            user.is_superuser = True
        else:
            user.is_superuser = False
        user.save()