# user/serializers.py
from rest_framework import serializers
from .models import User, Address

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'first_name', 'last_name', 'phone')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
        )
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name', 'phone', 'avatar', 'role')
        read_only_fields = ('email', 'role')  # email и роль нельзя менять


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            'id', 'title', 'full_name', 'phone', 'address_line',
            'city', 'postal_code', 'country', 'is_default', 'created_at'
        )
        read_only_fields = ('created_at',)

    def validate(self, attrs):
        # Можно добавить валидацию почтового индекса, телефона и т.п.
        return attrs