# shop/tests.py
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from user.models import User
from shop.models import Product, Category, CartItem, Order

class ProductListTest(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Laptop",
            slug="laptop",
            category=self.category,
            price=1000,
            stock=10
        )

    def test_get_products(self):
        url = reverse('product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class CartTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='cart@test.com', password='123', username='cart')
        self.category = Category.objects.create(name="Books", slug="books")
        self.product = Product.objects.create(
            name="Book",
            slug="book",
            category=self.category,
            price=20,
            stock=5
        )
        self.client.login(email='cart@test.com', password='123')

    def test_add_to_cart(self):
        url = reverse('cart-add')
        data = {'product_id': self.product.id, 'quantity': 2}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(CartItem.objects.first().quantity, 2)


class OrderCreationTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='order@test.com', password='123', username='order')
        self.category = Category.objects.create(name="Tech", slug="tech")
        self.product = Product.objects.create(
            name="Phone",
            slug="phone",
            category=self.category,
            price=500,
            stock=5
        )
        self.address = self.user.addresses.create(
            full_name="Ivan",
            phone="+79991234567",
            address_line="Main St, 1",
            city="Moscow",
            postal_code="123456"
        )
        self.cart_item = CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        self.client.login(email='order@test.com', password='123')

    def test_create_order(self):
        url = reverse('create-order')
        data = {'address_id': self.address.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().user, self.user)