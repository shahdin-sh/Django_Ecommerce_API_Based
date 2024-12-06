from .imports import *


class OrderViewSet(ModelViewSet):
    filter_backends = [OrderingFilter, SearchFilter, DjangoFilterBackend]
    filterset_class = OrderFilter
    search_fields = ['customer__user__username']
    ordering_fields = ['datetime_created']
    pagination_class = StandardResultSetPagination

    def is_manager(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name='Order Manager').exists()

    def get_queryset(self):
        queryset = Order.objects.prefetch_related(
            Prefetch('items', OrderItem.objects.select_related('product')),
        ).select_related('customer__user', 'customer__address').order_by('-datetime_created')
        
        return queryset.all() if self.is_manager() else queryset.filter(customer__user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrderCreationSerializer
        
        return ManagerOrderSerializer if self.is_manager() else OrderSerializer
     
    def create(self, request, *args, **kwargs):
        order_creation_serializer = OrderCreationSerializer(data=request.data, context={'request': self.request})
        order_creation_serializer.is_valid(raise_exception=True)
        created_order = order_creation_serializer.save()
        
        if self.is_manager():
          serializer = ManagerOrderSerializer(created_order)
        else:  
            serializer = OrderSerializer(created_order)

        return Response(serializer.data , status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        order = self.get_object()

        # Trigger the Celery task to increase products inventory asynchronously
        task_list = group(
            update_inventory.s(orderitem.product.id, orderitem.quantity, False) for orderitem in order.items.all()
        )
        task_list.apply_async()

        return super().destroy(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method in ['DELETE', 'PATCH', 'PUT']:
            return [IsOrderManager()]
        return [IsAuthenticated()]
    
    def get_throttles(self):
      self.throttle_scope = 'order'
      return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Order Manager')
