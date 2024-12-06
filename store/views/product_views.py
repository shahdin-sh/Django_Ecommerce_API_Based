from .imports import *


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    lookup_field = 'slug'
    queryset = Product.objects.prefetch_related('comments').select_related('category').annotate(
        comments_count=Count('comments')
        ).all().order_by('-id')
    filter_backends = [SearchFilter, OrderingFilter , DjangoFilterBackend]
    filterset_class = ProductFilter
    ordering_fields = ['name', 'inventory', 'unit_price']
    search_fields = ['name', 'category__title']
    pagination_class = LargeResultSetPagination
    permission_classes = [IsProductManager]

    CACHE_KEY_PREFIX = "product_list"

    @method_decorator(cache_page(60 * 15, key_prefix=CACHE_KEY_PREFIX))
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)

        if page:
            serializer = self.get_serializer(page, many=True)
            paginated_response = self.get_paginated_response(serializer.data)

            return paginated_response
    
    def retrieve(self, request, *args, **kwargs):
        # custom caching to get the product slug dynamically
        product_slug = kwargs.get('slug')
        product_cache = cache.get(product_slug)

        if product_cache:
            return Response(product_cache)
        
        try:
            product = self.get_queryset().get(slug=product_slug)
            serializer = ProductSerializer(product, context={'request': request})

            # cache serialized product before returning the response 
            cache.set(product_slug, serializer.data, 60 * 15)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            raise NotFound()

    def destroy(self, request, slug):
        product = get_object_or_404(Product.objects.select_related('category').all(), slug=slug)
        if product.order_items.count() > 0:
            return Response(
                f'{product.name} referenced through protected foreign key: {[orderitem for orderitem in product.order_items.all()]}', 
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )

        product.delete()
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    def get_throttles(self):
        self.throttle_scope = 'product'
        return base_throttle.get_throttles(
            request=self.request, 
            throttle_scope=self.throttle_scope, 
            group_name='Product Manager'
        )
    

class CategoryViewSet(ModelViewSet):
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    queryset = Category.objects.all().annotate(
            # with annotate method, products_count is known as a Category field when this view is called.
            products_count = Count('products')
        ).prefetch_related('products').order_by('-products_count')
    filter_backends = [DjangoFilterBackend]
    filterset_fields  = ['title']
    pagination_class = StandardResultSetPagination
    permission_classes = [IsProductManager]

    def destroy(self, request, slug):
        category = get_object_or_404(Category.objects.all().annotate(products_count = Count('products')), slug=slug)
        if category.products.count() > 0:
            return Response(
                f'{category.title} referenced through protected foreign key: {[product for product in category.products.all()]}', 
                status=status.HTTP_405_METHOD_NOT_ALLOWED
            )
        
        category.delete()
        return Response(status=status.HTTP_404_NOT_FOUND)
    
    def get_throttles(self):
        self.throttle_scope = 'category'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Product Manager')
    
    
class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    lookup_field = 'pk'
    filter_backends = [OrderingFilter]
    ordering_fields = ['datetime_created', 'name']
    pagination_class = StandardResultSetPagination
    permission_classes = [IsContentManager]

    def get_queryset(self):
        return Comment.objects.select_related('product').filter(
            product__slug=self.kwargs['product_slug'], status=Comment.COMMENT_STATUS_APPROVED).order_by('-datetime_created')
    
    def get_serializer_context(self):
        context = {
            'product' : Product.objects.get(slug=self.kwargs['product_slug'])
        }
        return context
    
    def get_throttles(self):
        self.throttle_scope = 'comment'
        return base_throttle.get_throttles(self.request, throttle_scope=self.throttle_scope, group_name='Content Manager')