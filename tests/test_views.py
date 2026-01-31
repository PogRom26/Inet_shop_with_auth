import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_checkout_page_requires_login(client):
    url = reverse("checkout")
    response = client.get(url)
    assert response.status_code == 302
    assert "/login/" in response.url


@pytest.mark.django_db
def test_checkout_page_authenticated(authenticated_client):
    url = reverse("checkout")
    response = authenticated_client.get(url)
    assert response.status_code == 200