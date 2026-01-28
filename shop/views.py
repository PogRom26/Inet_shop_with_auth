# shop/views.py
from .models import Order, OrderItem, CartItem
from user.models import Address
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Product, CartItem
from .serializers import CartItemSerializer

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from weasyprint import HTML
import tempfile

from rest_framework import generics
from .serializers import ProductSerializer
from .filters import ProductFilter
from pagination import StandardResultsSetPagination

import django_filters

from django.shortcuts import render

class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Получаем данные
        address_id = request.data.get('address_id')
        comment = request.data.get('comment', '')

        # Проверяем адрес
        address_obj = get_object_or_404(Address, id=address_id, user=request.user)
        address_text = (
            f"{address_obj.full_name}, "
            f"{address_obj.phone}, "
            f"{address_obj.address_line}, "
            f"{address_obj.city}, {address_obj.postal_code}, {address_obj.country}"
        )

        # Получаем элементы корзины
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response(
                {"error": "Корзина пуста"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Рассчитываем общую сумму
        total_price = sum(item.product.price * item.quantity for item in cart_items)

        # Создаём заказ
        order = Order.objects.create(
            user=request.user,
            address=address_text,
            total_price=total_price,
            status='pending'
        )

        # ... после создания order и order.items ...

        # Генерация PDF
        context = {'order': order}
        html_string = render_to_string('invoice.html', context)
        html = HTML(string=html_string)
        pdf_file = html.write_pdf()

        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(pdf_file)
            temp_pdf_path = temp_pdf.name

        # Отправляем email
        try:
            send_mail(
                subject=f'Ваш счёт №{order.id}',
                message=f'Здравствуйте!\n\nБлагодарим за заказ №{order.id} на сумму {order.total_price} ₽.\n\nСчёт во вложении.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,
                html_message=f"""
                <p>Здравствуйте!</p>
                <p>Благодарим за заказ <strong>№{order.id}</strong> на сумму <strong>{order.total_price} ₽</strong>.</p>
                <p>Счёт во вложении.</p>
                <p>С уважением,<br>Команда InetShop</p>
                """
            )

            # Прикрепляем PDF
            from django.core.mail import EmailMessage
            email = EmailMessage(
                subject=f'Ваш счёт №{order.id}',
                body='Счёт во вложении.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[request.user.email],
            )
            email.attach('schet_{}.pdf'.format(order.id), pdf_file, 'application/pdf')
            email.send()

        except Exception as e:
            # Логируем ошибку (можно использовать logging)
            print(f"Ошибка отправки email: {e}")
            # Но не прерываем заказ!


        # Создаём позиции заказа (с фиксацией цены!)
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
                total_price=item.product.price * item.quantity,
            )
            # Опционально: уменьшаем остаток на складе
            # item.product.stock -= item.quantity
            # item.product.save()

        # Очищаем корзину
        cart_items.delete()

        return Response({
            "detail": "Заказ успешно оформлен",
            "order_id": order.id,
            "total_price": total_price,
            "status": order.status
        }, status=status.HTTP_201_CREATED)

# Отмена заказа
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

        # Проверяем наличие на складе
        if quantity > product.stock:
            return Response(
                {'error': f'Недостаточно товара на складе. Доступно: {product.stock}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем или создаём элемент корзины
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


class UserOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).prefetch_related('items').order_by('-created_at')

        # Применяем пагинацию
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
            product = get_object_or_404(Product, id=item.product.id)  # Предполагаем, что OrderItem ссылается на Product
            # Но у нас сейчас OrderItem — денормализованная копия
            # Поэтому ищем по имени (или лучше добавить product_id в OrderItem)

            # ⚠️ ВАЖНО: сейчас OrderItem не имеет связи с Product!
            # Решение: либо добавить ForeignKey, либо искать по имени (ненадёжно)
            # Лучше — модифицировать модель!

            # Пока предположим, что мы можем найти товар по имени
            try:
                product = Product.objects.get(name=item.product_name, is_active=True)
            except Product.DoesNotExist:
                errors.append(f"Товар '{item.product_name}' больше не доступен")
                continue

            # Проверяем наличие
            available = min(item.quantity, product.stock)
            if available == 0:
                errors.append(f"Товар '{item.product_name}' закончился")
                continue

            # Добавляем в корзину
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




class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True).select_related('category')
    serializer_class = ProductSerializer
    filter_backends = [
        django_filters.rest_framework.DjangoFilterBackend,
        'rest_framework.filters.SearchFilter',
    ]
    filterset_class = ProductFilter
    search_fields = ['name', 'description']


def index(request):
    return render(request, 'index.html')

def products_page(request):
    return render(request, 'products.html')

def cart_page(request):
    return render(request, 'cart.html')

def profile_page(request):
    return render(request, 'profile.html')