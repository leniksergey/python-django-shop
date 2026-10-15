from django.contrib.auth import get_user_model
from django.test import TestCase

from accounts.models import Profile

User = get_user_model()


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(username="tester", password="pass12345")
        self.assertEqual(user.username, "tester")
        self.assertTrue(user.check_password("pass12345"))

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            username="admin2", password="pass12345",
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)


class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="profile_user", password="pass12345",
        )

    def test_profile_created(self):
        profile = Profile.objects.create(user=self.user)
        self.assertEqual(profile.user, self.user)
        self.assertFalse(profile.archived)

    def test_display_name_falls_back_to_username(self):
        profile = Profile.objects.create(user=self.user)
        self.assertEqual(profile.display_name, "profile_user")

    def test_display_name_strips_email_domain(self):
        user = User.objects.create_user(
            username="user@example.com", password="pass12345",
        )
        profile = Profile.objects.create(user=user)
        self.assertEqual(profile.display_name, "user")

    def test_display_name_uses_full_name(self):
        self.user.first_name = "Иван"
        self.user.last_name = "Петров"
        self.user.save()
        profile = Profile.objects.create(user=self.user)
        self.assertEqual(profile.display_name, "Иван Петров")
