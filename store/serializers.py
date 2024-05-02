from rest_framework import serializers
from django.utils.text import slugify
from .models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(
        view_name = 'category_detail',
        lookup_field = 'slug'
    )
    num_of_products = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['title', 'description', 'num_of_products', 'detail']
    
    # methods
    def get_num_of_products(self, obj:Category):
        return obj.products_count


    # for POST HTTP Method
    def create(self, validated_data):
        category = Category(**validated_data)
        category.slug = slugify(category.title)
        category.save()
        return category
    
    # for PUT HTTP Method
    def update(self, instance, validated_data):
        # update the instance with validated data
        instance = super().update(instance, validated_data)

        instance.slug = slugify(instance.title)
        instance.save()

        return instance
    
        


class ProductSerializer(serializers.ModelSerializer):
    title = serializers.CharField(max_length=255, source='name')
    detail = serializers.HyperlinkedIdentityField(
        view_name= 'product_detail',
        lookup_field = 'slug'
    )
    category = serializers.HyperlinkedRelatedField(
        queryset = Category.objects.all(),
        view_name = 'category_detail',
        lookup_field = 'slug'
    )
    price = serializers.DecimalField(max_digits=6, decimal_places=2, source='unit_price')
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['title', 'price', 'total_price', 'inventory', 'category', 'detail']

    DOLLAR_SIGN = '$'
    def get_total_price(self, obj:Product):
        total_price = int(obj.unit_price * obj.inventory)
        return f'{total_price} {self.DOLLAR_SIGN}'
    
    def create(self, validated_data):
        product = Product(**validated_data)
        product.slug = slugify(product.name)
        product.save()
        return product
    
    def update(self, instance, validated_data):
        # update the instance with validated data
        instance = super().update(instance, validated_data)

        instance.slug = slugify(instance.name)
        instance.save()

        return instance