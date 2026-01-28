# user/urls.py
from django.urls import path
from . import views
from user.views import LogoutView, LoginView

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    # Адреса
    path('addresses/', views.AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('addresses/set-default/<int:pk>/', views.SetDefaultAddressView.as_view(), name='set-default-address'),

    # Вход
    path('login/', LoginView.as_view(), name='login'),
    # Выход
    path('logout/', views.LogoutView.as_view(), name='logout'),
]