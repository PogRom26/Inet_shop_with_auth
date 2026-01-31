from django.test import TestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class UserTestCase(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(
            email="client@site.com",
            password="securepass"
        )
        self.assertEqual(user.email, "client@site.com")
        self.assertTrue(user.check_password("securepass"))
        self.assertFalse(user.is_superuser)

    def test_user_string_representation(self):
        user = User(email="client@site.com")
        self.assertEqual(str(user), "client@site.com")