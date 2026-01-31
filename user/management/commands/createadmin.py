from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Создаёт суперпользователя по умолчанию'

    def handle(self, *args, **options):
        User = get_user_model()
        email = 'admin@example.com'
        password = 'admin'
        username = 'admin'

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                username=username,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f'Суперпользователь {email} успешно создан')
            )
        else:
            self.stdout.write(f'Суперпользователь {email} уже существует')