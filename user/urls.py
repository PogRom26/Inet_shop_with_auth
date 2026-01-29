from django.urls import path
from . import views

app_name = 'user'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='profile_api'),  # ← Только API
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    # Адреса
    path('addresses/', views.AddressListView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', views.AddressDetailView.as_view(), name='address-detail'),
    path('addresses/set-default/<int:pk>/', views.SetDefaultAddressView.as_view(), name='set-default-address'),
    # Выход
    path('logout/', views.LogoutView.as_view(), name='logout'),
]