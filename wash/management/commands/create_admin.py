from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = "Create an admin user if it doesn't already exist"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not email or not password:
            self.stdout.write(self.style.WARNING("Superuser environment variables not set."))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS("Superuser already exists."))
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

        self.stdout.write(self.style.SUCCESS("Superuser created successfully."))