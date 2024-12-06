from .imports import *


class WishlistViewSet(ModelViewSet):
    http_method_names = ['get', 'delete', 'options', 'head']
    lookup_field = 'id'
    serializer_class = WishlistSerializer
    pagination_class = StandardResultSetPagination

    def is_admin_or_manager(self):
        user = self.request.user
        if user.is_authenticated and (user.is_superuser or user.groups.filter(name='Product Manager').exists()):
            return True

    def get_queryset(self):
        user = self.request.user
        queryset = Wishlist.objects.select_related('user').prefetch_related('products')

        if self.is_admin_or_manager():
            return queryset.all().order_by('user__id')
        return queryset.filter(user=user)
    
    def paginate_queryset(self, queryset):
        if self.is_admin_or_manager():
            return super().paginate_queryset(queryset)
    
    def get_permissions(self):
        if self.request.method in ['DELETE']:
            return [IsProductManager()]
        return [IsAuthenticated()]


class AddToWishlistView(ViewSet):
    http_method_names = ['post']

    @transaction.atomic()
    def create(self, request, product_slug:None):
        user_wishlist, created = Wishlist.objects.get_or_create(user=request.user)
        
        product_slug = self.kwargs['product_slug']
        product = Product.objects.get(slug=product_slug)

        if product not in user_wishlist.products.all():
            user_wishlist.products.add(product)
            user_wishlist.save()
            return Response(
                f'Product {product.name} added to your wishlist successfully',
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(
                f'Product {product.name} has already added to your wishlist',
                status=status.HTTP_400_BAD_REQUEST
            )


class WishlistProductView(ViewSet):
    http_method_names = ['get', 'delete', 'options', 'head']
    permission_classes = [IsAuthenticated]

    def get_queryset(self, wishlist_id):
        user = self.request.user
        
        try:
            queryset = Wishlist.objects.select_related('user').prefetch_related('products').get(
                id = wishlist_id,
                user = user
            )
            return queryset
        except Wishlist.DoesNotExist:
            raise NotFound()
    
    def list(self, request, wishlist_id=None):
        queryset = self.get_queryset(wishlist_id).products.all()
        serializer = WishlistProductSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, wishlist_id:None, pk):
        queryset = self.get_queryset(wishlist_id)

        try:
            product = queryset.products.get(id=pk)
            serializer = WishlistProductSerializer(product, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            raise NotFound()
    
    def destroy(self, request, wishlist_id:None, pk):
        queryset = self.get_queryset(wishlist_id)

        try:
            product = queryset.products.get(id=pk)

            queryset.products.remove(product)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Product.DoesNotExist:
            raise NotFound()