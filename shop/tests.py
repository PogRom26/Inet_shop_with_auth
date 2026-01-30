from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import Category, Product, CartItem, Order, OrderItem

User = get_user_model()

class ShopModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass12345'
        )
        self.category = Category.objects.create(name='Электроника')
        self.product = Product.objects.create(
            category=self.category,
            name='Смартфон',
            price=Decimal('29990.00'),
            stock=10
        )

    def test_create_product(self):
        self.assertEqual(self.product.name, 'Смартфон')
        self.assertEqual(self.product.price, Decimal('29990.00'))

    def test_add_to_cart(self):
        cart_item = CartItem.objects.create(
            user=self.user,
            product=self.product,
            quantity=2
        )
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.total_price, Decimal('59980.00'))

    def test_create_order(self):
        order = Order.objects.create(
            user=self.user,
            address='ул. Примерная, д. 1',
            delivery_type='delivery',
            total_price=Decimal('29990.00'),
            status='pending'
        )
        self.assertEqual(order.status, 'pending')
        self.assertIn('Примерная', order.address)


class ShopAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass12345'
        )
        self.category = Category.objects.create(name='Одежда')
        self.product = Product.objects.create(
            category=self.category,
            name='Куртка',
            price=Decimal('8990.00'),
            stock=5
        )

    def test_jwt_token(self):
        url = reverse('token_obtain_pair')
        data = {'email': 'test@example.com', 'password': 'pass12345'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_add_to_cart_api(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('cart-add')
        data = {'product_id': self.product.id, 'quantity': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_get_cart(self):
        self.client.force_authenticate(user=self.user)
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        url = reverse('cart-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['product_name'], 'Куртка')

    def test_create_order(self):
        self.client.force_authenticate(user=self.user)
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        url = reverse('create-order')
        data = {'address': 'ул. Ленина, д. 10', 'delivery_type': 'delivery'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

    def test_create_order_empty_cart(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('create-order')
        data = {'address': 'ул. Ленина, д. 10', 'delivery_type': 'delivery'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Корзина пуста', response.data['error'])

    def test_insufficient_stock(self):
        self.client.force_authenticate(user=self.user)
        # Пробуем добавить больше, чем есть на складе
        url = reverse('cart-add')
        data = {'product_id': self.product.id, 'quantity': 10}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)  # Добавится, но проверим при заказе

        # Оформляем заказ
        url_order = reverse('create-order')
        data_order = {'address': 'ул. Ленина', 'delivery_type': 'delivery'}
        response_order = self.client.post(url_order, data_order, format='json')
        self.assertEqual(response_order.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Недостаточно товара', response_order.data['error'])


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email='user@example.com',
            password='pass12345'
        )
        self.assertEqual(user.email, 'user@example.com')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)