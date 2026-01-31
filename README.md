# Интернет-магазин с авторизацией

## Описание
Django + DRF + JWT + Docker. Полноценный интернет-магазин с регистрацией, входом, корзиной и админкой.

## Технологии
- Django REST Framework
- JWT
- PostgreSQL
- Docker
- OpenAPI (Redoc)

## Запуск
bash cp .env.example .env docker-compose up --build
## Админка
- URL: `/admin/`
- Логин: `admin@example.com`
- Пароль: `admin`

## API
- Документация: `/api/docs/`
- Логин: `POST /api/token/`
- Регистрация: `POST /api/auth/register/`

