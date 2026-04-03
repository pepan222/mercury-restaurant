from django.db import models
from django.contrib.auth.models import User

class Review(models.Model):
    """Отзыв клиента"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Клиент')
    rating = models.IntegerField('Оценка', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])
    comment = models.TextField('Отзыв')
    is_moderated = models.BooleanField('Промодерирован', default=False)
    is_published = models.BooleanField('Опубликован', default=False)
    created_at = models.DateField('Дата', auto_now_add=True)
    
    class Meta:
        db_table = 'reviews'
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Отзыв от {self.user.username} - {self.rating}★'
