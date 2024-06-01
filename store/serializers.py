from rest_framework import serializers

from django.utils.text import slugify
from django.shortcuts import get_object_or_404
from django.db import transaction 

from .models import Product, Category, Comment, Cart, CartItem, Customer, Address, Order, OrderItem


class CategorySerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name = 'category-detail', lookup_field = 'slug')
    num_of_products = serializers.IntegerField(source='products_count', read_only=True)

    class Meta:
        model = Category
        fields = ['title', 'description', 'num_of_products', 'detail']

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
        fields = ['id', 'name', 'body', 'datetime_created']

    def create(self, validated_data):
        product_id = self.context['product'].id
        self.instance = Comment.objects.create(product_id=product_id, **validated_data)
        return self.instance


class ProductSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=255, source='name')
    detail = serializers.HyperlinkedIdentityField(view_name='product-detail', lookup_field = 'slug')
    category = serializers.HyperlinkedRelatedField(queryset=Category.objects.all(), view_name = 'category-detail', lookup_field = 'slug')
    price = serializers.DecimalField(max_digits=6, decimal_places=2, source='unit_price')
    total_price = serializers.SerializerMethodField()
    num_of_comments = serializers.IntegerField(source='comments_count', read_only=True)
    comments = CommentSerializer(many=True, read_only=True) # Nested serializer for comments

    class Meta:
        model = Product
        fields = ['title', 'price', 'category', 'inventory', 'total_price', 'num_of_comments', 'detail', 'comments']

    DOLLAR_SIGN = '$'

    def get_total_price(self, obj:Product):
        total_price = f'{int(obj.unit_price * obj.inventory): ,}'
        return f'{total_price} {self.DOLLAR_SIGN}'
    
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
 

# Cart Serializers
class CartProductSerializer(serializers.ModelSerializer):

    detail = serializers.HyperlinkedIdentityField(view_name='product-detail', lookup_field = 'slug')

    class Meta:
        model = Product
        fields = ['name', 'inventory', 'unit_price', 'detail']
    
    
# handle cart items creation (POST request)
class AddItemtoCartSerializer(serializers.ModelSerializer):

    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = CartItem
        fields = ['product', 'quantity']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cart = self.context.get('cart')

        cart_product_ids = []
        try:
            for item in cart.items.all():
                cart_product_ids.append(item.product.id)

            self.fields['product'].queryset = Product.objects.exclude(id__in=cart_product_ids)
        except AttributeError:
            return None

    def create(self, validated_data):
        cart_id = self.context['cart'].id
        product = validated_data['product']
        quantity = validated_data['quantity']

        #  Perform custom validation checks 
        if quantity < 1:
            raise serializers.ValidationError('quantity must be greater or equal to 1')
        elif  quantity > product.inventory:
            raise serializers.ValidationError(f'quantity must be less than {product.name} inventory')
        else:
            self.instance = CartItem.objects.create(cart_id=cart_id, **validated_data)
            return self.instance
        

# handle cart items update and view (GET and PUT request)
class CartItemSerializer(serializers.ModelSerializer):

    current_product_stock = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    product = CartProductSerializer(read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity', 'current_product_stock', 'total_price']
        read_only_fields = ['quantity']

    DOLLAR_SIGN = '$'

    def get_current_product_stock(self, obj:CartItem):
        return obj.product.inventory - obj.quantity 

    def get_total_price(self, obj:CartItem):
        total_price = (obj.quantity * int(obj.product.unit_price))
        return f'{total_price: ,} {self.DOLLAR_SIGN}'

    def update(self, instance, validated_data):
        #  Perform custom validation checks 
        if validated_data['quantity'] < 1:
            raise serializers.ValidationError('quantity must be greater or equal to 1')
        elif  validated_data['quantity'] > instance.product.inventory:
            raise serializers.ValidationError(f'quantity must be less than {instance.product} inventory')
        else:
            super().update(instance, validated_data)
            instance.save()
            return instance


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_price']

    DOLLAR_SIGN = '$'

    def get_total_price(self, obj:Cart):
        total_price = sum([item.quantity * int(item.product.unit_price) for item in obj.items.all()])
        return f'{total_price: ,} {self.DOLLAR_SIGN}'
    

# Address Serializers
class AddressDetailSerializer(serializers.ModelSerializer):
    customer = serializers.HyperlinkedRelatedField(view_name='customer-detail', lookup_field='pk', read_only=True)

    class Meta:
        model = Address
        fields = ['customer', 'province', 'city', 'street']


class AddressListSerializer(serializers.ModelSerializer):

    customer = serializers.HyperlinkedRelatedField(view_name='customer-detail', lookup_field='pk', read_only=True)
    detail = serializers.HyperlinkedIdentityField(view_name='address-detail', lookup_field='pk')

    class Meta:
        model = Address
        fields = ['detail', 'customer', 'province', 'city', 'street']


# Customer Serializers
class CustomerAddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['province', 'city', 'street']
    
    
class CustomerSerializer(serializers.ModelSerializer):

    address = CustomerAddressSerializer(read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'user', 'birth_date', 'address']
    
    def get_user(self, obj:Customer):
        return obj.user.username


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

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price', 'total_price']

    DOLLAR_SIGN = '$'

    def get_product(self, obj:OrderItem):
        return obj.product.name
    
    def get_total_price(self, obj:OrderItem):
        return f'{obj.quantity * obj.unit_price} {self.DOLLAR_SIGN}'
    

class AdminOrderSerializer(serializers.ModelSerializer):

    customer = CustomerOrderSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    total_items_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'datetime_created', 'status', 'total_items_price', 'customer', 'items']
    
    DOLLAR_SIGN = '$'

    def get_total_items_price(self, obj:Order):
        return f'{sum([item.quantity * item.unit_price for item in obj.items.all()])} {self.DOLLAR_SIGN}'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_items_price = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'datetime_created', 'status', 'total_items_price', 'items']
        read_only_fields = ['status']
    
    DOLLAR_SIGN = '$'

    def get_total_items_price(self, obj:Order):
        return f'{sum([item.quantity * item.unit_price for item in obj.items.all()])} {self.DOLLAR_SIGN}'


class OrderCreationSerializer(serializers.Serializer):
    cart_uuid = serializers.UUIDField()

    def validate_cart_uuid(self, cart_uuid):
        try: 
            cart_obj = Cart.objects.prefetch_related('items').get(id=cart_uuid)

            # check if any items exists in the cart or not
            if cart_obj.items.count() == 0:
                raise serializers.ValidationError('You must at least have one item in your cart.')
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
            # first way
            for item in cart_obj.items.all():
                OrderItem.objects.create(
                    order = order_obj,
                    product = item.product,
                    quantity = item.quantity,
                    unit_price = item.product.unit_price
                )
                
            # order_items = [
            #     OrderItem(
            #         order = order_obj,
            #         product = item.product,
            #         quantity = item.quantity,
            #         unit_price = item.product.unit_price
            #     ) for item in cart_obj.items.all()
            # ]

            # OrderItem.objects.bulk_create(order_items)

            # cart_obj.delete()

            return order_obj
            