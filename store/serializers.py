from rest_framework import serializers
from django.utils.text import slugify
from .models import Product, Category, Comment


class CategorySerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name = 'category-detail', lookup_field = 'slug')
    num_of_products = serializers.IntegerField(source='products_count', read_only=True)

    class Meta:
        model = Category
        fields = ['title', 'description', 'num_of_products', 'detail']
    
    # # methods
    # def get_num_of_products(self, obj:Category):
    #     return obj.products_count


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
    

class CommentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['id', 'name', 'body', 'datetime_created']

    def create(self, validated_data):
        product_id = self.context['product'].id
        return Comment.objects.create(product_id=product_id, **validated_data)


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
        return product
    
    def update(self, instance, validated_data):
        # update the instance with validated data
        instance = super().update(instance, validated_data)

        instance.slug = slugify(instance.name)
        instance.save()

        return instance