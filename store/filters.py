from django_filters import rest_framework as filters
from .models import Product


class ProductFilter(filters.FilterSet):

    INVENTORY_STATUS_CHOICE = (
        ('Critical', 'critical'),
        ('Medium', 'medium'),
        ('Good', 'good')
    )

    inventory_lte = filters.NumberFilter(field_name='inventory', lookup_expr='lte')
    inventory_gte = filters.NumberFilter(field_name='inventory', lookup_expr='gte')
    min_price = filters.NumberFilter(field_name='unit_price', lookup_expr='lte')
    max_price = filters.NumberFilter(field_name='unit_price', lookup_expr='lte')
    inventory_status = filters.ChoiceFilter(
        choices=INVENTORY_STATUS_CHOICE, 
        method='filter_by_inventory_status',
        label='Inventory status'
    )

    class Meta:
        model = Product
        fields = ['inventory_lte', 'inventory_gte', 'min_price', 'max_price', 'category__slug', 'inventory_status']

    def filter_by_inventory_status(self, queryset, name, value):
        if value == 'Critical':
            return queryset.filter(inventory__lte=10)
        
        if value == 'Medium':
            return queryset.filter(inventory__range=[10, 50])
        
        if value == 'Good':
            return queryset.filter(inventory__gte=50)
       
