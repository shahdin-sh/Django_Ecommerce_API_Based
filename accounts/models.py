from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    email = models.EmailField(blank=True, unique=True, verbose_name='email address')
    phone_number = PhoneNumberField(blank=True, region='IR')

    def clean(self):
        super().clean()
        if CustomUser.objects.filter(phone_number=self.phone_number).count() > 1:
              raise ValidationError({'phone_number': 'Phone number must be unique.'})
