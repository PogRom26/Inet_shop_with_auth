import pytest
from decimal import Decimal
from shop.models import Category, Product, CartItem, Order


@pytest.mark.django_db
def test_create_category():
    category = Category.objects.create(name="Электроника")
    assert str(category) == "Электроника"


@pytest.mark.django_db
def test_create_product():
    category = Category.objects.create(name="Электроника")
    product = Product.objects.create(
        category=category,
        name="Смартфон",
        price=Decimal("29990.00"),
        stock=10,
    )
    assert product.name == "Смартфон"
    assert product.get_absolute_url() == f"/product/{product.id}/"


@pytest.mark.django_db
def test_cart_item_total_price():
    user = User.objects.create_user(email="user@test.com", password="123")
    category = Category.objects.create(name="Одежда")
    product = Product.objects.create(
        category=category,
        name="Куртка",
        price=Decimal("8990.00"),
        stock=5,
    )
    cart_item = CartItem.objects.create(user=user, product=product, quantity=2)
    assert cart_item.total_price == Decimal("17980.00")


@pytest.mark.django_db
def test_order_total_price():
    user = User.objects.create_user(email="user@test.com", password="123")
    order = Order.objects.create(
        user=user,
        address="ул. Ленина, д. 10",
        delivery_type="delivery",
        total_price=Decimal("29990.00"),
    )
    assert order.status == "pending"
    assert order.items.count() == 0