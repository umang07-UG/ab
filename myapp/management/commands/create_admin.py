from django.core.management.base import BaseCommand
from myapp.models import User


class Command(BaseCommand):
    help = 'Create admin user if not exists'

    def handle(self, *args, **kwargs):
        admin_email    = 'admin1@gmail.com'
        admin_password = '12'
        admin_name     = 'Admin'

        if not User.objects.filter(email=admin_email).exists():
            User.objects.create(
                name=admin_name,
                email=admin_email,
                password=admin_password,
                mobile=0
            )
            self.stdout.write(self.style.SUCCESS(f'Admin user created: {admin_email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Admin user already exists: {admin_email}'))
