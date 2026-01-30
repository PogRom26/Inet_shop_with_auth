from django.shortcuts import render, redirect
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import tempfile

from .models import Product, CartItem, Order, OrderItem, Category
from .serializers import CartItemSerializer, ProductSerializer, CategorySerializer
from .filters import ProductFilter
from config.pagination import StandardResultsSetPagination
from user.models import Address


# === API: Заказы ===
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CartItem, Order, OrderItem
from django.shortcuts import get_object_or_404

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        address = request.data.get('address')
        comment = request.data.get('comment', '')

        if not address:
            return Response({'error': 'Адрес обязателен'}, status=400)

        # Получаем корзину пользователя
        cart_items = CartItem.objects.filter(user=request.user).select_related('product')
        if not cart_items.exists():
            return Response({'error': 'Корзина пуста'}, status=400)

        total_price = 0
        order_items_data = []

        # Проверка каждого товара
        for item in cart_items:
            if not item.product:
                continue  # Пропускаем, если товар удалён

            if item.quantity > item.product.stock:
                return Response({
                    'error': f'Недостаточно товара "{item.product.name}" на складе'
                }, status=400)

            total_price += item.product.price * item.quantity
            order_items_data.append(item)

        # Создаём заказ
        try:
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_price=total_price,
                comment=comment,
                status='pending'
            )
        except Exception as e:
            return Response({'error': f'Ошибка создания заказа: {str(e)}'}, status=500)

        # Добавляем товары в заказ
        for item in order_items_data:
            if not item.product:
                continue

            try:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                # Уменьшаем остаток
                item.product.stock -= item.quantity
                item.product.save()
                # Удаляем из корзины
                item.delete()
            except Exception as e:
                return Response({'error': f'Ошибка при добавлении товара: {str(e)}'}, status=500)

        return Response({'order_id': order.id}, status=201)


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


from rest_framework import status

class CartAddView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id, available=True)

        if quantity <= 0:
            return Response({'error': 'Количество должно быть больше 0'}, status=status.HTTP_400_BAD_REQUEST)
        if quantity > product.stock:
            return Response(
                {'error': f'Недостаточно на складе. Максимум: {product.stock}'},
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
                    {'error': f'Можно добавить ещё: {product.stock - cart_item.quantity}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart_item.quantity = new_quantity
            cart_item.save()

        serializer = CartItemSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

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
            "comment": order.comment,
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
                product = Product.objects.get(name=item.product_name, available=True)
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
    queryset = Product.objects.filter(available=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardResultsSetPagination
    filterset_class = ProductFilter

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def get_paginated_response(self, data):
        return Response({
            'count': self.paginator.page.paginator.count,
            'total_pages': self.paginator.page.paginator.num_pages,
            'current_page': self.paginator.page.number,
            'results': data,
            'links': {
                'next': self.paginator.get_next_link(),
                'previous': self.paginator.get_previous_link(),
            }
        })


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(available=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


# === HTML-страницы ===
def index(request):
    return render(request, 'index.html')


def products_page(request):
    return render(request, 'products.html')


def product_detail_page(request, product_id):
    return render(request, 'product_detail.html')


def login_page(request):
    return render(request, 'login.html')


def register_page(request):
    return render(request, 'register.html')


def profile_page(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'profile.html')


def cart_page(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'cart.html')


def order_detail_page(request, order_id):
    return render(request, 'order_detail.html')


def orders_history_page(request):
    if not request.user.is_authenticated:
        return redirect('/login/')
    return render(request, 'orders_history.html')


def checkout_page(request):
    return render(request, 'checkout.html')