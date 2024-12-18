from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.timezone import now

from . import models


class InventoryFilter(admin.SimpleListFilter):
    ZERO = '0'
    LESS_THAN_10 = '<10'
    BETWEEN_10_and_30 = '10<=30'
    MORE_THAN_30 = '>30'
    title = 'Critical Inventory Status'
    parameter_name = 'inventory'

    def lookups(self, request, model_admin):
        return [
            (InventoryFilter.ZERO, 'OUT Of Stock'),
            (InventoryFilter.LESS_THAN_10, 'High'),
            (InventoryFilter.BETWEEN_10_and_30, 'Medium'),
            (InventoryFilter.MORE_THAN_30, 'OK'),
        ]
    
    def queryset(self, request, queryset):
        if self.value() == InventoryFilter.ZERO:
            return queryset.filter(inventory__exact=0)
        if self.value() == InventoryFilter.LESS_THAN_10:
            return queryset.filter(inventory__lt=10).order_by('inventory')
        if self.value() == InventoryFilter.BETWEEN_10_and_30:
            return queryset.filter(inventory__range=(10, 30)).order_by('-inventory')
        if self.value() == InventoryFilter.MORE_THAN_30:
            return queryset.filter(inventory__gt=30).order_by('-inventory')


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'inventory', 'unit_price', 'activation', 'inventory_status', 'product_category', 'num_of_comments']
    list_per_page = 10
    list_editable = ['unit_price']
    list_select_related = ['category']
    list_filter = ['datetime_created', 'activation' ,InventoryFilter]
    actions = ['clear_inventory']
    search_fields = ['name', ]
    prepopulated_fields = {
        'slug': ['name', ]
    }

    def get_queryset(self, request):
        return super().get_queryset(request) \
                .prefetch_related('comments') \
                .annotate(
                    comments_count=Count('comments'),
                )

    def inventory_status(self, product):
        if product.inventory < 10:
            return 'Low'
        if product.inventory > 50:
            return 'High'
        return 'Medium'
    
    @admin.display(description='# comments', ordering='comments_count')
    def num_of_comments(self, product):
        url = (
            reverse('admin:store_comment_changelist') 
            + '?'
            + urlencode({
                'product__id': product.id,
            })
        )
        return format_html('<a href="{}">{}</a>', url, product.comments_count)
        
    
    @admin.display(ordering='category__title')
    def product_category(self, product):
        return product.category.title

    
    @admin.action(description='Clear inventory')
    def clear_inventory(self, request, queryset):
        update_count = queryset.update(inventory=0)
        self.message_user(
            request,
            f'{update_count} of products inventories cleared to zero.',
            messages.ERROR,
        )


admin.site.register(models.Category)
    

@admin.register(models.Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'status', ]
    list_editable = ['status']
    list_per_page = 10
    search_fields = ['name',]
    autocomplete_fields = ['product', ]


@admin.register(models.Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user']
    readonly_fields = ['user', 'products']
    ordering = ['user__id']


# Cart & CartItem inlince and registration
class CartItemInline(admin.TabularInline):
    model = models.CartItem
    list_display = ['id', 'product', 'quantity']
    extra = 0
    min_num = 1

    def get_queryset(self, request):
        pass


@admin.register(models.Cart)
class CartAdmin(admin.ModelAdmin):
    # cart obj just can be created by authenticated and anon users who send Post Requests.
    list_display = ['id', 'user', 'session_key', 'created_at']
    readonly_fields = ['id', 'created_at', 'user', 'session_key']
    ordering = ['-created_at']
    inlines = [CartItemInline]


# Customer & Address inlince and registration
class AddressInline(admin.TabularInline):
    model = models.Address
    fiedls  = ['province', 'street', 'city']
    extra = 0
    min_num = 1


@admin.register(models.Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [ 'customer_username', 'email', 'phone_number', 'address']
    list_per_page = 10
    ordering = ['user__username']
    search_fields = ['user__username']
    inlines = [AddressInline]

    def customer_username(self, obj):
        return obj.user.username

    def email(self, obj):
        return obj.user.email
    
    def phone_number(self, obj):
        return obj.user.phone_number
    
    def address(self, obj):
        return obj.address.objects.all()


# Order & OrderItem inlince and registration
class OrderItemInline(admin.TabularInline):
    model = models.OrderItem
    fields = ['product', 'quantity', 'unit_price']
    extra = 0
    min_num = 1


@admin.register(models.Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'datetime_created', 'num_of_items', 'expiration']
    list_editable = ['status']
    list_per_page = 10
    ordering = ['-datetime_created']
    inlines = [OrderItemInline]

    def get_queryset(self, request):
        return super() \
                .get_queryset(request) \
                .prefetch_related('items') \
                .annotate(
                    items_count=Count('items')
                )

    @admin.display(ordering='items_count', description='# items')
    def num_of_items(self, order):
        return order.items_count
    
    @admin.display(description='expired_in')
    def expiration(self, order):
        if order.status == 'paid':
            return 'Approved'
        
        # celery-beat has been scheduled to delete expired orders every 10 mins 
        if order.is_expired:
            return 'Expired'
        
        remaining_time_in_sec = int((order.expires_at - now()).total_seconds())
        remaining_time_in_min =  remaining_time_in_sec // 60
        if remaining_time_in_min == 0:
            return f'{remaining_time_in_sec} Seconds' 
        else:
            return f'{remaining_time_in_min} Minutes'


@admin.register(models.OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    readonly_fields = ['order', 'product', 'quantity', 'unit_price']
    autocomplete_fields = ['product', ]


    


