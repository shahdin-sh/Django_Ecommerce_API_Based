from rest_framework import permissions
from django.contrib.auth.models import Group
from copy import deepcopy


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.method in permissions.SAFE_METHODS or (request.user and request.user.is_staff))


class IsAdminMixin:
    def has_admin_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

class IsAdminOrReadOnlyMixin:
    def has_read_only_or_admin_permission(self, request, view):
        return bool(request.method in permissions.SAFE_METHODS or (request.user and request.user.is_staff))

class GroupCheckMixin:
    def check_users_group(self, request, view, group_name):
        try:
            return bool(Group.objects.get(name=group_name) in request.user.groups.all()) 
        except Group.DoesNotExist:
            return False


# Other Permission classes that use above mixins
class IsProductManager(permissions.BasePermission, IsAdminOrReadOnlyMixin, GroupCheckMixin):
    def has_permission(self, request, view):
        if self.has_read_only_or_admin_permission(request, view) or self.check_users_group(request, view, 'Product Manager'):
            return True


class IsContentManager(permissions.BasePermission, IsAdminOrReadOnlyMixin):
    def has_permission(self, request, view):
        if self.has_read_only_or_admin_permission(request, view) or self.check_users_group(request, view, 'Content Manager'):
            return True


class IsCustomerManager(permissions.BasePermission, IsAdminMixin, GroupCheckMixin):
    def has_permission(self, request, view):
        if self.has_admin_permission(request, view) or self.check_users_group(request, view, 'Customer Manager'):
            return True
        
        return bool(request.user and request.user.has_perm('store.send_private_email'))


class IsUserManager(permissions.BasePermission, IsAdminMixin, GroupCheckMixin):
    def has_permission(self, request, view):
        if self.has_admin_permission(request, view) or self.check_users_group(request, view, 'User Manager'):
            return True
        

# class CustomDjangoModelPermission(permissions.DjangoModelPermissions):
#     def __init__(self):
#         self.perms_map['GET'] = deepcopy(self.perms_map['GET'])
#         self.perms_map['GET'] = ['%(app_label)s.view_%(model_name)s']