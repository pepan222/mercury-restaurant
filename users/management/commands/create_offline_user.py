from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Profile


class Command(BaseCommand):
    help = 'Создает пользователя для очных клиентов'

    def handle(self, *args, **options):
        username = 'offline_client'
        email = 'offline@mercury.ru'
        password = 'offline_client_2024'
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name='Очный',
                last_name='клиент'
            )
            Profile.objects.get_or_create(user=user, defaults={'phone': 'Не указан'})
            self.stdout.write(self.style.SUCCESS(f'Пользователь "{username}" создан'))
        else:
            self.stdout.write(self.style.WARNING(f'Пользователь "{username}" уже существует'))