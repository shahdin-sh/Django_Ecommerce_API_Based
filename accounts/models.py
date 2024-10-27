from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    email = models.EmailField(blank=True, unique=True, verbose_name='email address')
    phone_number = PhoneNumberField(blank=True ,region='IR')
