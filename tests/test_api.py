import pytest
from rest_framework import status
from django.urls import reverse
from decimal import Decimal


@pytest.mark.django_db
def test_jwt_token(api_client):
    User.objects.create_user(email="test@example.com", password="pass12345")
    url = reverse("token_obtain_pair")
    response = api_client.post(
        url,
        {"email": "test@example.com", "password": "pass12345"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    assert "access" in response.data


@pytest.mark.django_db
def test_add_to_cart_api(authenticated_client):
    url = reverse("cart-add")
    data = {"product_id": 1, "quantity": 2}
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code in [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST]


@pytest.mark.django_db
def test_get_cart(authenticated_client):
    url = reverse("cart-list")
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_create_order_empty_cart(authenticated_client):
    url = reverse("create-order")
    data = {"address": "ул. Ленина", "delivery_type": "delivery"}
    response = authenticated_client.post(url, data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Корзина пуста" in response.data["error"]