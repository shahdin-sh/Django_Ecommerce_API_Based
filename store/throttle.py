from rest_framework.throttling import BaseThrottle, UserRateThrottle, AnonRateThrottle, ScopedRateThrottle
from rest_framework import views
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import Group
from django.conf import settings


class AdminUserThrottle(BaseThrottle):
    def allow_request(self, request, view):
        return True

class BaseThrottleView(views.APIView):
    throttle_classes = [UserRateThrottle, AnonRateThrottle, ScopedRateThrottle, AdminUserThrottle]

    # group name and throttle scope must me str and they are optional 
    def get_throttles(self, request, group_name=None, throttle_scope=None):
        # validate group_name and throttle scope 
        self.validation(group_name=group_name, throttle_scope=throttle_scope)    

        if request.user.is_superuser or request.user.groups.filter(name='admin').exists(): 
            return [AdminUserThrottle()]
        
        # throttle scope should set in the view and scoped rate throttle only can used by managers 
        if request.user.groups.filter(name=group_name).exists():
            return [ScopedRateThrottle()]
        
        if request.user.is_authenticated:
            return [UserRateThrottle()]
        
        # except the above statements means anon users
        return [AnonRateThrottle()]
    
    def validation(self, group_name, throttle_scope):
        throttle_rates =  list(settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', {}).keys())
        valid_group_names = list(Group.objects.values_list('name', flat=True))

        if group_name and group_name not in valid_group_names:
            raise ValidationError(f'Invalid group name: {group_name}, options are: {valid_group_names}')
        
        if throttle_scope and throttle_scope not in throttle_rates:
            raise ValidationError(f'invalid throttle rate: {throttle_scope}, options are: {throttle_rates}')
            
