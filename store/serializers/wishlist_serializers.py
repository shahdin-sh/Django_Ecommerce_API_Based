from .imports import *


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