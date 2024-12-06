from .imports import *


class ManagersAddAddressSerializer(serializers.ModelSerializer):
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all())

    class Meta:
        model = Address
        fields = ['customer', 'province', 'city', 'street']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)
        # Filter customers who do not have any associated addresses
        self.fields['customer'].queryset = Customer.objects.filter(address__isnull=True).distinct()


class ManagerAddressSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    customer = serializers.HyperlinkedRelatedField(view_name='customer-detail', lookup_field='pk', read_only=True)
    detail = serializers.HyperlinkedIdentityField(view_name='address-detail', lookup_field='pk')

    class Meta:
        model = Address
        fields = ['pk', 'user', 'detail', 'customer', 'province', 'city', 'street']

    def get_user(self, obj:Address):
        return obj.customer.user.username


class AddAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['province', 'city', 'street']
    
    def validate(self, data):
        request = self.context.get('request')
        address_instance = Address.objects.select_related('customer').filter(customer__user=request.user)

        if address_instance.exists():
            raise serializers.ValidationError('address has already created.')
        return data
        
    def create(self, validated_data):
        request = self.context['request']
        customer = Customer.objects.select_related('user').prefetch_related('address').get(user=request.user)

        address = Address.objects.create(customer=customer, **validated_data)
        self.instance = address
        return address    


class AddressSerializer(serializers.ModelSerializer):
    detail = serializers.HyperlinkedIdentityField(view_name='address-detail', lookup_field='pk')

    class Meta:
        model = Address
        fields = ['province', 'city', 'street', 'detail']

    
class CustomerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['province', 'city', 'street']


class ManagerCustomerSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    address = CustomerAddressSerializer(read_only=True)
    address_creation_endpoint = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'user', 'birth_date', 'address', 'address_creation_endpoint']
    
    def get_user(self, obj:Customer):
        return obj.user.username
    
    def get_address_creation_endpoint(self, obj:Customer):
        search_url = (SITE_URL_HOST + reverse('address-list') + f'?search={obj.user.username}')
        address = Address.objects.filter(customer=obj)
        
        if address.exists():
            return None
        return search_url 
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        address = Address.objects.filter(customer=instance)

        if address.exists():
            representation.pop('address_creation_endpoint', None)

        return representation
    

class CustomerSerializer(serializers.ModelSerializer):
    address = CustomerAddressSerializer(read_only=True)
    address_info = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['birth_date', 'address', 'address_info']
    
    def get_address_info(self, obj:Customer):
        url = (SITE_URL_HOST + reverse('address-list'))
        address = Address.objects.filter(customer=obj)

        if address.exists():
            return url + f'{obj.id}/'
        
        return url + f'?search={obj.user.username}'