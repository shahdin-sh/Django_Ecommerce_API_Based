from django.contrib.auth import get_user_model

from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer

from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

User = get_user_model()

class DjoserCustomUserCreateSerializer(DjoserUserCreateSerializer):
    phone_number = PhoneNumberField(region='IR')

    class Meta(DjoserUserCreateSerializer.Meta):
        fields = ['username' ,'first_name', 'last_name', 'email', 'phone_number', 'password']


class DjoserCustomUserSerializer(DjoserUserSerializer):
    username = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = ['username', 'email', 'phone_number']
    
    def get_username(self, obj):
        if obj.username and obj.username[-1].isdigit():
            return obj.username
        return f'{obj.username}_{obj.id}'