from rest_framework import serializers

from .models import Product

def quantity_validation(product: Product, quantity: int):

    if quantity > product.inventory:
        raise serializers.ValidationError(
            f'quantity must be less than {product.name} inventory | < {product.inventory }'
        )
    if quantity < 1:
        raise serializers.ValidationError('quantity must be greater or equal to 1')
    
    return quantity