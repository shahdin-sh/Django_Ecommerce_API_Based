from rest_framework import serializers
from rest_framework.reverse import reverse

from django.db import transaction 
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.text import slugify

from config.urls import SITE_URL_HOST


from .models import Product, Category, Comment, Cart, CartItem, Customer, Address, Order, OrderItem, Wishlist
from .validations import quantity_validation


# Category Serializers
class CategoryProductsSerializer(serializers.ModelSerializer):
    unit_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['name', 'unit_price', 'inventory']

    TOMAN_SIGN = 'T'

    def get_unit_price(self, obj:Product):
        return f'{obj.clean_price} {self.TOMAN_SIGN}'


class CategorySerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name = 'category-detail', lookup_field = 'slug')
    num_of_products = serializers.IntegerField(source='products_count', read_only=True)
    products = CategoryProductsSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['title', 'description', 'num_of_products', 'detail', 'products']

    # for POST HTTP Method
    def create(self, validated_data):
        category = Category(**validated_data)
        category.slug = slugify(category.title)
        category.save()

        self.instance = category
        return category
    
    # for PUT HTTP Method
    def update(self, instance, validated_data):
        # update the instance with validated data
        instance = super().update(instance, validated_data)

        instance.slug = slugify(instance.title)
        instance.save()

        return instance
    

class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['id', 'name', 'body', 'status', 'datetime_created']

    def create(self, validated_data):
        product_id = self.context['product'].id
        self.instance = Comment.objects.create(product_id=product_id, **validated_data)
        return self.instance


class ProductSerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name='product-detail', lookup_field = 'slug')
    category = serializers.HyperlinkedRelatedField(queryset=Category.objects.all(), view_name = 'category-detail', lookup_field = 'slug')
    num_of_comments = serializers.IntegerField(source='comments_count', read_only=True)
    comments = CommentSerializer(many=True, read_only=True) # Nested serializer for comments

    class Meta:
        model = Product
        fields = ['name', 'unit_price', 'category', 'inventory', 'num_of_comments', 'detail', 'image', 'comments']
    
    def create(self, validated_data):
        product = Product(**validated_data)
        product.slug = slugify(product.name)
        product.save()

        self.instance = product
        return product
    
    def update(self, instance, validated_data):
        # update the instance with validated data
        instance = super().update(instance, validated_data)

        instance.slug = slugify(instance.name)
        instance.save()

        return instance

class WishlistProductSerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name='product-detail', lookup_field='slug')
    # wishlist_detail = serializers.HyperlinkedIdentityField(view_name='wishlist-products-detail', lookup_field='id')

    class Meta:
        model = Product
        fields = ['detail', 'id', 'name', 'unit_price', 'inventory', 'image']


class WishlistSerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name='wishlist-detail', lookup_field='id')
    products = WishlistProductSerializer(many=True ,read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id' ,'user', 'detail', 'products']
        read_only_fields = ['user']
 

# Cart Serializers
class CartProductSerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name='product-detail', lookup_field = 'slug')
    unit_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['name', 'inventory', 'unit_price', 'detail']
    
    TOMAN_SIGN = 'T'

    def get_unit_price(self, obj:Product):
        return f'{obj.clean_price} {self.TOMAN_SIGN}'


# Manager Cart & CartItem Serializer
class ManagerAddItemtoCartSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.active.all())

    class Meta:
        model = CartItem
        fields = ['product', 'quantity']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        cart_id = self.context['cart_id']
        cart_obj = Cart.objects.prefetch_related(
                        Prefetch('items', queryset=CartItem.objects.select_related('product'))
                    ).get(id=cart_id)
        
        cart_product_ids = list(cart_obj.items.values_list('product_id', flat=True))

        # exclude the products that is already in cart to prevent integirtiy error
        self.fields['product'].queryset = Product.objects.select_related('category').exclude(id__in=cart_product_ids)

    def validate(self, data):
        quantity_validation(data.get('product'), data.get('quantity'))
        return data
    
    def create(self, validated_data):
        cart_id = self.context['cart'].id

        cartitem = CartItem.objects.create(cart_id=cart_id, **validated_data)
        self.instance = cartitem
        return cartitem


class ManagerCartItemSerializer(serializers.ModelSerializer):
    current_product_stuck = serializers.SerializerMethodField()
    product = CartProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'current_product_stuck', 'total_price']

    def get_current_product_stuck(self, obj:CartItem):
        invenory = obj.product.inventory
        quantity = obj.quantity
        
        if invenory > quantity:
            return obj.product.inventory - obj.quantity 
        return 'Out of Stuck'

    def get_total_price(self, obj:CartItem):
        return obj.total_price()

    def update(self, instance, validated_data):

        quantity_validation(instance.product, validated_data['quantity'])

        super().update(instance, validated_data)
        instance.save()
        return instance
    

class ManagerCartSerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name='cart-detail', lookup_field='id', read_only=True)
    id = serializers.UUIDField(read_only=True)
    items = ManagerCartItemSerializer(many=True, read_only=True)
    belongs_to = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'belongs_to', 'detail', 'items', 'total_price']

    def get_total_price(self, obj:Cart):
        return obj.total_price()
    
    def get_belongs_to(self, obj:Cart):
        if obj.user:
            return (SITE_URL_HOST + reverse('customuser-detail', kwargs={'id': obj.user.id}))
        return f'anon user | {obj.session_key}'
    
    
# User Cart & CartItem Serializer
class AddItemtoCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ['quantity']

    def create(self, validated_data):
        product = Product.objects.get(slug=self.context['product_slug'])
        cart_id = self.context['cart_id']
        quantity = validated_data['quantity']

        quantity = quantity_validation(product, quantity)

        cartitem = CartItem.objects.create(cart_id=cart_id, product=product, quantity=quantity)
        self.instance = cartitem
        return cartitem
    

class CartItemSerializer(serializers.ModelSerializer):
    # detail = serializers.HyperlinkedRelatedField(view_name='cart-items-detail', lookup_field='pk', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    current_product_stuck = serializers.IntegerField(source='product.inventory', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product_name', 'quantity', 'current_product_stuck', 'total_price']

    def get_total_price(self, obj):
        return obj.total_price()

    def update(self, instance, validated_data):
        #  Perform custom validation checks 
        quantity_validation(instance.product, validated_data['quantity'])
        
        super().update(instance, validated_data)
        instance.save()
        return instance
    

class CartSerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name='cart-detail', lookup_field='id', read_only=True)
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'detail', 'items', 'total_price']
    
    def get_total_price(self, obj:Cart):
        return obj.total_price()
    


# Address Serializers
class AddressSerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name='address-detail', lookup_field='pk')

    class Meta:
        model = Address
        fields = ['province', 'city', 'street', 'detail']


class AddAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['province', 'city', 'street']
    
    def validate(self, data):
        request = self.context.get('request')
        address_instance = Address.objects.select_related('customer').filter(customer__user=request.user)

        if address_instance.exists():
            raise serializers.ValidationError('address has already created.')
        return data
        
    def create(self, validated_data):
        request = self.context['request']
        customer = Customer.objects.select_related('user').prefetch_related('address').get(user=request.user)

        address = Address.objects.create(customer=customer, **validated_data)
        self.instance = address
        return address    
    

class ManagerAddressSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    customer = serializers.HyperlinkedRelatedField(view_name='customer-detail', lookup_field='pk', read_only=True)
    detail = serializers.HyperlinkedIdentityField(view_name='address-detail', lookup_field='pk')

    class Meta:
        model = Address
        fields = ['pk', 'user', 'detail', 'customer', 'province', 'city', 'street']

    def get_user(self, obj:Address):
        return obj.customer.user.username


class ManagersAddAddressSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())

    class Meta:
        model = Address
        fields = ['customer', 'province', 'city', 'street']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        # Filter customers who do not have any associated addresses
        self.fields['customer'].queryset = Customer.objects.filter(address__isnull=True).distinct()



# Customer Serializers
class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['province', 'city', 'street']


class ManagerCustomerSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    address = CustomerAddressSerializer(read_only=True)
    address_creation_endpoint = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'user', 'birth_date', 'address', 'address_creation_endpoint']
    
    def get_user(self, obj:Customer):
        return obj.user.username
    
    def get_address_creation_endpoint(self, obj:Customer):
        search_url = (SITE_URL_HOST + reverse('address-list') + f'?search={obj.user.username}')
        address = Address.objects.filter(customer=obj)
        
        if address.exists():
            return None
        return search_url 
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        address = Address.objects.filter(customer=instance)

        if address.exists():
            representation.pop('address_creation_endpoint', None)

        return representation
    

class CustomerSerializer(serializers.ModelSerializer):
    address = CustomerAddressSerializer(read_only=True)
    address_info = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['birth_date', 'address', 'address_info']
    
    def get_address_info(self, obj:Customer):
        url = (SITE_URL_HOST + reverse('address-list'))
        address = Address.objects.filter(customer=obj)

        if address.exists():
            return url + f'{obj.id}/'
        
        return url + f'?search={obj.user.username}'


class CustomerOrderSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=255, source='user.username')
    address = serializers.CharField(max_length=255)

    class Meta:
        model = Customer
        fields = ['id', 'username', 'address']



# Order Serializers
class OrderItemSerializer(serializers.ModelSerializer):

    product = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    unit_price = serializers.CharField(source='clean_price')

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price', 'total_price']

    TOMAN_SIGN = 'T'

    def get_product(self, obj:OrderItem):
        return obj.product.name
    
    def get_total_price(self, obj:OrderItem):
        total_price = obj.quantity * obj.unit_price
        return f'{total_price: ,} {self.TOMAN_SIGN}'
    

class ManagerOrderSerializer(serializers.ModelSerializer):

    customer = CustomerOrderSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total_items_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'datetime_created', 'status', 'total_items_price', 'customer', 'items']
    
    TOMAN_SIGN = 'T'

    def get_total_items_price(self, obj:Order):
        total_order_items_price = sum([item.quantity * item.unit_price for item in obj.items.all()])
        return f'{total_order_items_price: ,} {self.TOMAN_SIGN}'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_items_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'datetime_created', 'status', 'total_items_price', 'items']
        read_only_fields = ['status']
    
    TOMAN_SIGN = 'T'

    def get_total_items_price(self, obj:Order):
        total_order_items_price = sum([item.quantity * item.unit_price for item in obj.items.all()])
        return f'{total_order_items_price: ,} {self.TOMAN_SIGN}'


class OrderCreationSerializer(serializers.Serializer):
    cart_uuid = serializers.UUIDField()

    def validate_cart_uuid(self, cart_uuid):
        try: 
            Cart.objects.prefetch_related('items').get(id=cart_uuid)
            return cart_uuid
        except Cart.DoesNotExist:
            raise serializers.ValidationError('cart object not found')
    
    def save(self, **kwargs):
        with transaction.atomic():
            # access cart from the validated data
            cart_id = self.validated_data['cart_uuid']
            cart_obj = Cart.objects.prefetch_related('items').get(id=cart_id)
            # creating order obj 
            customer = Customer.objects.select_related('user').get(user=self.context['request'].user)
            order_obj = Order.objects.create(customer=customer)

            # create orderitems based on the items in cart that user fill its uuid
                
            order_items = [
                OrderItem(
                    order = order_obj,
                    product = item.product,
                    quantity = item.quantity,
                    unit_price = item.product.unit_price
                ) for item in cart_obj.items.all()
            ]

            OrderItem.objects.bulk_create(order_items)

            cart_obj.delete()

            return order_obj


# Payment Serializer
class PaymentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()

    def validate(self, data):
        order_id = data['order_id']
        request = self.context.get('request')
        error_messages = {
            'not_exists_ms': f'Order with id {order_id} does not exist.',
            'already_paid_ms': f'Order with id {order_id} is already paid.'
        }

        try:
            order_id = data['order_id']
            order = Order.objects.select_related('customer').prefetch_related('items').get(id=order_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError(error_messages['not_exists_ms'])
        
        if order.customer.user != request.user:
            raise serializers.ValidationError(error_messages['not_exists_ms'])
        
        if order.status != Order.ORDER_STATUS_UNPAID:
            raise serializers.ValidationError(error_messages['already_paid_ms'])
        
        return data