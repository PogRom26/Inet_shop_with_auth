# user/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class User(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Пользователь'),
        ('manager', 'Менеджер'),
        ('admin', 'Администратор'),
    )

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    @property
    def is_user(self):
        return self.role == 'user'

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_admin(self):
        return self.role == 'admin'


class Address(models.Model):
    user = models.ForeignKey(
        'User',
        related_name='addresses',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    title = models.CharField('Название адреса', max_length=50, blank=True)  # например: "Дом", "Работа"
    full_name = models.CharField('ФИО получателя', max_length=100)
    phone = models.CharField('Телефон', max_length=15)
    address_line = models.CharField('Адрес', max_length=255)
    city = models.CharField('Город', max_length=100)
    postal_code = models.CharField('Почтовый индекс', max_length=10)
    country = models.CharField('Страна', max_length=100, default='Россия')
    is_default = models.BooleanField('По умолчанию', default=False)

    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Адрес'
        verbose_name_plural = 'Адреса'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.full_name} – {self.address_line}, {self.city}"

    def save(self, *args, **kwargs):
        # Если этот адрес помечен как default — снимаем флаг с других
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)