# shop/serializers.py
from rest_framework import serializers
from .models import CartItem, Product, Category

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


from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.SlugField(source='category.slug', read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'category', 'category_name', 'category_slug',
            'description', 'price', 'stock', 'image_url', 'is_active'
        )

    def get_image_url(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            return obj.image.url
        return None

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')