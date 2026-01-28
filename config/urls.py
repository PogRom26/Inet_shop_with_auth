# myproject/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView
from shop.views import index, products_page, cart_page, profile_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('user.urls')),
    path('api/shop/', include('shop.urls')),
    # JWT стандартные эндпоинты
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API Schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Redoc (красивая документация)
    path('api/docs/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('', index, name='home'),
    path('products/', products_page, name='products'),
    path('cart/', cart_page, name='cart_page'),
    path('profile/', profile_page, name='profile_page'),
]