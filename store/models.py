import hashlib
from typing import Iterable
from django.db import models
from django.utils.text import slugify
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.conf import settings
from uuid import uuid4


class Category(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.CharField(max_length=500, blank=True)
    top_product = models.ForeignKey('Product', on_delete=models.SET_NULL, blank=True, null=True, related_name='+')

    def __str__(self):
        return self.title


class Discount(models.Model):
    discount = models.FloatField()
    description = models.CharField(max_length=255)

    def __str__(self):
        return f'{str(self.discount)} | {self.description}'


class ActiveProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(activation=True)


class Product(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    slug = models.SlugField(unique=True)
    description = models.TextField()
    unit_price = models.PositiveIntegerField()
    inventory = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    datetime_created = models.DateTimeField(auto_now_add=True)
    datetime_modified = models.DateTimeField(auto_now=True)
    discounts = models.ManyToManyField(Discount, blank=True)
    activation = models.BooleanField(default=True)
    image = models.ImageField(upload_to='sample/', blank=True, null=True)

    objects = models.Manager()
    active = ActiveProductManager()

    def __str__(self):
        return self.name
    
    @property
    def clean_price(self):
        return f'{self.unit_price: ,}'


class Customer(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        user = self.user
        
        if user.first_name and user.last_name:
            return f'{user.first_name} {user.last_name}' 
        return f'{user.username}'
    
    class Meta:
        permissions = [
            ('send_private_email', 'Can send private email to user by the button')
        ]


class Address(models.Model):
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, primary_key=True, related_name='address')
    province = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    street = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.city} city, {self.province} province, {self.street} street.'


class UnpaidOrderManger(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Order.ORDER_STATUS_UNPAID)


class Order(models.Model):
    ORDER_STATUS_PAID = 'paid'
    ORDER_STATUS_UNPAID = 'unpaid'
    ORDER_STATUS_CANCELED = 'canceled'
    ORDER_STATUS = [
        (ORDER_STATUS_PAID,'Paid'),
        (ORDER_STATUS_UNPAID,'Unpaid'),
        (ORDER_STATUS_CANCELED,'Canceled'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='orders')
    datetime_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255, choices=ORDER_STATUS, default=ORDER_STATUS_UNPAID)

    objects = models.Manager()
    unpaid_orders = UnpaidOrderManger()

    def __str__(self):
        return f'Order id={self.id}'
    
    @property
    def total_items_price(self):
        return sum([item.unit_price * item.quantity for item in self.items.all()])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveSmallIntegerField()
    unit_price = models.PositiveIntegerField()

    class Meta:
        unique_together = [['order', 'product']]

    def __str__(self):
        return f'item_{self.id} | belongs to order_{self.order.id}'
    
    @property
    def clean_price(self):
        return f'{self.unit_price: ,}'


class CommentManger(models.Manager):
    def get_approved(self):
        return self.get_queryset().filter(status=Comment.COMMENT_STATUS_APPROVED)


class ApprovedCommentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Comment.COMMENT_STATUS_APPROVED)


class Comment(models.Model):
    COMMENT_STATUS_WAITING = 'waiting'
    COMMENT_STATUS_APPROVED = 'approved'
    COMMENT_STATUS_NOT_APPROVED = 'not approved'
    COMMENT_STATUS = [
        (COMMENT_STATUS_WAITING, 'Waiting'),
        (COMMENT_STATUS_APPROVED, 'Approved'),
        (COMMENT_STATUS_NOT_APPROVED, 'Not Approved'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=255)
    body = models.TextField()
    datetime_created = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, choices=COMMENT_STATUS, default=COMMENT_STATUS_WAITING)

    objects = CommentManger()
    approved = ApprovedCommentManager()


class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    session_key = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f'{self.id} | {self.user.username}'
        return f'{self.id} | {self.session_key[:4]}...'
    
    TOMAN_SIGN = 'T'

    def total_price(self):
        cart_total_price = sum((item.product.unit_price * item.quantity) for item in self.items.all())

        return f'{cart_total_price: ,} {self.TOMAN_SIGN}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        unique_together = [['cart', 'product']]
    
    TOMAN_SIGN = 'T'
    
    def total_price(self):
        cartitem_total_price =  sum([self.product.unit_price * self.quantity])

        return f'{cartitem_total_price: ,} {self.TOMAN_SIGN}'


class Wishlist(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField('Product', blank=True, null=True)

    def __str__(self):
        return f'{self.user} wishlist'