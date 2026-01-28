# shop/serializers.py
from rest_framework import serializers
from .models import CartItem, Product

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.SerializerMethodField(read_only=True)
    total_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = (
            'id', 'product', 'product_name', 'product_price',
            'product_image', 'quantity', 'total_price'
        )

    def get_product_image(self, obj):
        request = self.context.get('request')
        if obj.product.image:
            return request.build_absolute_uri(obj.product.image.url) if request else obj.product.image.url
        return None

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

# shop/serializers.py
class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'category', 'category_name',
            'description', 'price', 'stock', 'image_url', 'is_active'
        )

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image:
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None