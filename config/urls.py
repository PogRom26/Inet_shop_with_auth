from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

from shop.views import (
    index,
    products_page,
    product_detail_page,
    login_page,
    register_page,
    profile_page,
    cart_page,
    order_detail_page,
    orders_history_page,
)

urlpatterns = [
    # === Админка ===
    path('admin/', admin.site.urls),  # 🔥 Обязательно!

    # === API: Авторизация и JWT ===
    path('api/auth/', include('user.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # === API: Магазин ===
    path('api/shop/', include('shop.urls')),

    # === API: Документация ===
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # === HTML-страницы ===
    path('', index, name='home'),
    path('products/', products_page, name='products'),
    path('product/<int:product_id>/', product_detail_page, name='product_detail'),
    path('login/', login_page, name='login'),
    path('register/', register_page, name='register'),
    path('profile/', profile_page, name='profile'),
    path('cart/', cart_page, name='cart'),
    path('order/<int:order_id>/', order_detail_page, name='order_detail'),
    path('orders-history/', orders_history_page, name='orders_history'),
]