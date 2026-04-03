from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    """Профиль пользователя (расширение стандартного User)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    phone = models.CharField('Телефон', max_length=20, blank=True)
    address = models.TextField('Адрес доставки', blank=True)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
