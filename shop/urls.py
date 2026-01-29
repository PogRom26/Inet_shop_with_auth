from django.urls import path
from . import views
from user.views import RegisterView

app_name = 'shop'

urlpatterns = [
    # === API: корзина ===
    path('cart/', views.CartListView.as_view(), name='cart-list'),
    path('cart/add/', views.CartAddView.as_view(), name='cart-add'),
    path('cart/update/<int:pk>/', views.CartUpdateView.as_view(), name='cart-update'),
    path('cart/remove/<int:pk>/', views.CartRemoveView.as_view(), name='cart-remove'),

    # === API: заказы ===
    path('create-order/', views.CreateOrderView.as_view(), name='create-order'),
    path('cancel-order/<int:order_id>/', views.CancelOrderView.as_view(), name='cancel-order'),
    path('orders/', views.UserOrdersView.as_view(), name='user-orders'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:order_id>/repeat/', views.RepeatOrderView.as_view(), name='repeat-order'),

    # === API: каталог ===
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
]