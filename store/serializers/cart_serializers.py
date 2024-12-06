from .imports import *


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