from .imports import *


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