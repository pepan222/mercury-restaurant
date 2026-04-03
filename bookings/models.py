from django.db import models
from django.contrib.auth.models import User

class Table(models.Model):
    """Стол в ресторане"""
    table_number = models.IntegerField('Номер стола', unique=True)
    seats = models.IntegerField('Количество мест')
    location = models.CharField('Расположение', max_length=50, default='Зал')
    is_active = models.BooleanField('Активен', default=True)
    
    class Meta:
        db_table = 'tables'
        verbose_name = 'Стол'
        verbose_name_plural = 'Столы'
    
    def __str__(self):
        return f'Стол №{self.table_number} ({self.seats} мест)'

class Reservation(models.Model):
    """Бронирование столика"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтверждено'),
        ('cancelled', 'Отменено'),
        ('completed', 'Завершено'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Клиент')
    table = models.ForeignKey(Table, on_delete=models.CASCADE, verbose_name='Стол')
    reservation_date = models.DateField('Дата бронирования')
    reservation_time = models.TimeField('Время')
    guest_count = models.IntegerField('Количество гостей')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateField('Дата создания', auto_now_add=True)
    
    class Meta:
        db_table = 'reservations'
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-reservation_date', 'reservation_time']
    
    def __str__(self):
        return f'Бронь {self.user.username} на {self.reservation_date} {self.reservation_time}'
