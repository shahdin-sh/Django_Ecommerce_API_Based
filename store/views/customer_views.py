from .imports import *


class CustomerViewSet(ModelViewSet):
    # each new user has customer model so post method is not allowed
    http_method_names = ['get', 'put', 'head', 'options']
    serializer_class = ManagerCustomerSerializer
    queryset = Customer.objects.select_related('user').prefetch_related('address').order_by('id')
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_class = CustomerWithOutAddress
    search_fields = ['user__username']
    pagination_class = StandardResultSetPagination
    permission_classes = [IsCustomerManager]

    @action(detail=False, methods=['GET', 'PUT', 'HEAD', 'OPTIONS'], permission_classes=[IsAuthenticated])
    def me(self, request):
         # no need of get_object_or_404 because of customer creation signal for newly signed up users
        customer = Customer.objects.select_related('user').get(user=request.user)
        if request.method == 'GET':
            serializer = CustomerSerializer(customer, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        elif request.method == 'PUT':
            serializer = CustomerSerializer(customer, request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(status=status.HTTP_200_OK)
        
        elif request.method == 'HEAD':
            return Response(status=status.HTTP_200_OK)
        
        elif request.method == 'OPTIONS':
            # Respond with allowed methods and other OPTIONS-related headers
            return Response(status=status.HTTP_200_OK)
         
    def get_throttles(self):
      self.throttle_scope = 'customer'
      return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Customer Manager')


class AddressViewSet(ModelViewSet):
    filter_backends = [SearchFilter]
    search_fields = ['customer__user__username']
    pagination_class = None

    def is_manager(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Customer Manager').exists()

    def get_queryset(self):
        queryset = Address.objects.select_related('customer__user').order_by('pk')
       
        return queryset.all() if self.is_manager() else queryset.filter(customer__user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ManagersAddAddressSerializer if self.is_manager() else AddAddressSerializer
        elif self.request.method == 'PUT':
            return AddressSerializer
        else:
            return ManagerAddressSerializer if self.is_manager() else AddressSerializer
    
    def create(self, request, *args, **kwargs):
        if self.is_manager():
            creation_serializer = ManagersAddAddressSerializer
            serializer = ManagerAddressSerializer
        else:
            creation_serializer = AddAddressSerializer
            serializer = AddressSerializer
        
        creation_serializer = creation_serializer(data=request.data, context={'request': request})
        creation_serializer.is_valid(raise_exception=True)
        created_address = creation_serializer.save()

        serializer = serializer(created_address, context={'request': request})

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        if self.is_manager():
            self.pagination_class = StandardResultSetPagination
            page = self.paginate_queryset(queryset)

            if page:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset ,many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def get_permissions(self):
        if self.request.method == 'DELETE':
            return [IsCustomerManager()]
        return [IsAuthenticated()]
    
    def get_throttles(self):    
        self.throttle_scope = 'address'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Customer Manager')
    