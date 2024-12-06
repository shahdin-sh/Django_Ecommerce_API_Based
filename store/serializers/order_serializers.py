from .imports import *


class CustomerOrderSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=255, source='user.username')
    address = serializers.CharField(max_length=255)

    class Meta:
        model = Customer
        fields = ['id', 'username', 'address']


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