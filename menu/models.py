from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField('Название', max_length=100, unique=True, db_index=True)
    description = models.TextField('Описание', blank=True)
    slug = models.SlugField('URL', unique=True, blank=True, db_index=True)
    order = models.IntegerField('Порядок сортировки', default=0, db_index=True)
    
    class Meta:
        db_table = 'category'
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['order', 'name']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Subcategory(models.Model):
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        verbose_name='Основная категория',
        related_name='subcategories',
        db_index=True
    )
    name = models.CharField('Название подкатегории', max_length=100, db_index=True)
    order = models.IntegerField('Порядок сортировки', default=0, db_index=True)
    
    class Meta:
        db_table = 'subcategory'
        verbose_name = 'Подкатегория'
        verbose_name_plural = 'Подкатегории'
        ordering = ['order', 'name']
        unique_together = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'order']),
            models.Index(fields=['category', 'name']),
        ]
    
    def __str__(self):
        return f'{self.category.name} → {self.name}'

class Dish(models.Model):
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        verbose_name='Основная категория',
        related_name='dishes',
        db_index=True
    )
    subcategory = models.ForeignKey(
        Subcategory, 
        on_delete=models.SET_NULL, 
        verbose_name='Подкатегория',
        null=True, 
        blank=True,
        related_name='dishes',
        db_index=True
    )
    name = models.CharField('Название', max_length=255, db_index=True)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField('Цена (₽)', max_digits=10, decimal_places=2, db_index=True)
    weight = models.CharField('Вес', max_length=50, blank=True, null=True)
    is_available = models.BooleanField('Доступно для заказа', default=True, db_index=True)
    order = models.IntegerField('Порядок сортировки', default=0, db_index=True)
    image = models.ImageField('Фото блюда', upload_to='dishes/', blank=True, null=True, help_text='Загрузите фото блюда')
    
    class Meta:
        db_table = 'dish'
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'
        ordering = ['category', 'subcategory', 'order', 'name']
        indexes = [
            models.Index(fields=['category', 'is_available']),
            models.Index(fields=['subcategory', 'is_available']),
            models.Index(fields=['is_available', 'order']),
        ]
    
    def __str__(self):
        return f'{self.name} - {self.price}₽'
    
    def get_image_url(self):
        if self.image:
            return self.image.url
        return '/static/images/logo.png'  # заглушка, если нет фото