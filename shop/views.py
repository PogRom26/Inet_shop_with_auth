from django.shortcuts import render
from rest_framework import status, permissions, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import tempfile

from .models import Product, CartItem, Order, OrderItem, Category
from .serializers import CartItemSerializer, ProductSerializer
from .filters import ProductFilter
from config.pagination import StandardResultsSetPagination
from user.models import Address  # ← важно: добавлен импорт


# === API: Заказы ===
class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        address_id = request.data.get('address_id')
        comment = request.data.get('comment', '')

        address_obj = get_object_or_404(Address, id=address_id, user=request.user)
        address_text = f"{address_obj.full_name}, {address_obj.phone}, {address_obj.address_line}, {address_obj.city}, {address_obj.postal_code}, {address_obj.country}"

        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"error": "Корзина пуста"}, status=status.HTTP_400_BAD_REQUEST)

        total_price = sum(item.product.price * item.quantity for item in cart_items)

        order = Order.objects.create(
            user=request.user,
            address=address_text,
            total_price=total_price,
            status='pending'
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
                total_price=item.product.price * item.quantity,
            )
            item.product.stock -= item.quantity
            item.product.save()

        cart_items.delete()

        return Response({
            "detail": "Заказ успешно оформлен",
            "order_id": order.id,
            "total_price": total_price,
            "status": order.status
        }, status=status.HTTP_201_CREATED)


class CancelOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.status in ['delivered', 'shipped']:
            return Response(
                {"error": "Нельзя отменить доставленный или отправленный заказ"},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'cancelled'
        order.save()
        return Response({"detail": "Заказ отменён"})


# === API: Корзина ===
class CartListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        serializer = CartItemSerializer(cart_items, many=True)
        return Response(serializer.data)


class CartAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id, is_active=True)

        if quantity <= 0:
            return Response({'error': 'Количество должно быть больше 0'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity > product.stock:
            return Response(
                {'error': f'Недостаточно товара на складе. Доступно: {product.stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item, created = CartItem.objects.get_or_create(
            user=request.user,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            new_quantity = cart_item.quantity + quantity
            if new_quantity > product.stock:
                return Response(
                    {'error': f'Нельзя добавить столько. Максимум: {product.stock - cart_item.quantity} шт.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity = new_quantity
            cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CartUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        cart_item = get_object_or_404(CartItem, id=pk, user=request.user)
        quantity = request.data.get('quantity')

        if not isinstance(quantity, int) or quantity <= 0:
            return Response({'error': 'Количество должно быть положительным числом'}, status=status.HTTP_400_BAD_REQUEST)

        if quantity > cart_item.product.stock:
            return Response(
                {'error': f'Недостаточно на складе. Максимум: {cart_item.product.stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_item.quantity = quantity
        cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data)


class CartRemoveView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        cart_item = get_object_or_404(CartItem, id=pk, user=request.user)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# === API: История заказов ===
class UserOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')
        paginator = StandardResultsSetPagination()
        paginated_orders = paginator.paginate_queryset(orders, request)

        data = [
            {
                "id": order.id,
                "created_at": order.created_at,
                "status": order.status,
                "total_price": order.total_price,
                "items_count": order.items.count(),
            }
            for order in paginated_orders
        ]
        return paginator.get_paginated_response(data)


class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, id=pk, user=request.user)
        items = [
            {
                "product_name": item.product_name,
                "price": item.price,
                "quantity": item.quantity,
                "total_price": item.total_price,
            }
            for item in order.items.all()
        ]
        return Response({
            "id": order.id,
            "created_at": order.created_at,
            "status": order.status,
            "total_price": order.total_price,
            "address": order.address,
            "items": items,
        })


class RepeatOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        added_count = 0
        errors = []

        for item in order.items.all():
            try:
                product = Product.objects.get(name=item.product_name, is_active=True)
            except Product.DoesNotExist:
                errors.append(f"Товар '{item.product_name}' больше не доступен")
                continue

            available = min(item.quantity, product.stock)
            if available == 0:
                errors.append(f"Товар '{item.product_name}' закончился")
                continue

            cart_item, created = CartItem.objects.get_or_create(
                user=request.user,
                product=product,
                defaults={'quantity': available}
            )
            if not created:
                new_qty = cart_item.quantity + available
                cart_item.quantity = min(new_qty, product.stock)
                cart_item.save()

            added_count += 1

        return Response({
            "detail": f"Заказ повторён: {added_count} товар(ов) добавлено в корзину",
            "errors": errors,
        }, status=status.HTTP_200_OK)


# === API: Каталог ===
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ['name', 'description']
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]  # ← обязательно!


@api_view(['GET'])
def category_list(request):
    categories = Category.objects.filter(is_active=True).values('id', 'name', 'slug')
    return Response(list(categories))


# === HTML-страницы (явные вьюхи) ===
def index(request):
    """Главная страница"""
    return render(request, 'index.html')


def products_page(request):
    """Страница каталога товаров"""
    return render(request, 'products.html')


def product_detail_page(request):
    """Страница деталей товара"""
    return render(request, 'product_detail.html')


def login_page(request):
    """Страница входа"""
    return render(request, 'login.html')


def register_page(request):
    """Страница регистрации"""
    return render(request, 'register.html')


def profile_page(request):
    """Личный кабинет"""
    return render(request, 'profile.html')


def cart_page(request):
    """Корзина"""
    return render(request, 'cart.html')


def order_detail_page(request):
    """Детали заказа"""
    return render(request, 'order_detail.html')


def orders_history_page(request):
    """История заказов"""
    return render(request, 'orders_history.html')