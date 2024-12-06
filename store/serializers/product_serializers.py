from .imports import *


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