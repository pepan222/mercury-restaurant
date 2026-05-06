from django.db import models
from django.contrib.auth.models import User
from menu.models import Dish

class Cart(models.Model):
    """Корзина пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    created_at = models.DateTimeField('Создана', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлена', auto_now=True)
    is_active = models.BooleanField('Активна', default=True)
    
    class Meta:
        db_table = 'carts'
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
    
    def __str__(self):
        return f'Корзина {self.user.username}'
    
    def get_total(self):
        """Общая сумма корзины"""
        total = 0
        for item in self.items.all():
            total += item.dish.price * item.quantity
        return total

class CartItem(models.Model):
    """Товар в корзине"""
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items', verbose_name='Корзина')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, verbose_name='Блюдо')
    quantity = models.PositiveIntegerField('Количество', default=1)
    
    class Meta:
        db_table = 'cart_items'
        verbose_name = 'Товар в корзине'
        verbose_name_plural = 'Товары в корзине'
        unique_together = [['cart', 'dish']]
    
    def __str__(self):
        return f'{self.dish.name} x{self.quantity}'
    
    def get_total(self):
        return self.dish.price * self.quantity

class Order(models.Model):
    """Заказ"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('confirmed', 'Подтвержден'),
        ('preparing', 'Готовится'),
        ('delivering', 'Доставляется'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    
    PAYMENT_CHOICES = [
        ('cash', 'Наличными'),
        ('card', 'Картой онлайн'),
        ('card_courier', 'Картой курьеру'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    order_date = models.DateTimeField('Дата заказа', auto_now_add=True)
    total_amount = models.DecimalField('Сумма заказа', max_digits=10, decimal_places=2, default=0)
    delivery_cost = models.DecimalField('Стоимость доставки', max_digits=10, decimal_places=2, default=0)
    delivery_address = models.CharField('Адрес доставки', max_length=255)
    payment_method = models.CharField('Способ оплаты', max_length=20, choices=PAYMENT_CHOICES, default='cash')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    comment = models.TextField('Комментарий к заказу', blank=True)
    
    class Meta:
        db_table = 'orders'
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-order_date']
    
    def __str__(self):
        return f'Заказ №{self.id} - {self.user.username}'
    
    def get_subtotal(self):
        """Сумма заказа без доставки (только товары)"""
        return sum(item.get_total() for item in self.items.all())
    
    def get_final_amount(self):
        """Итоговая сумма с доставкой"""
        return self.get_subtotal() + self.delivery_cost

class OrderItem(models.Model):
    """Товар в заказе"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, verbose_name='Блюдо')
    quantity = models.PositiveIntegerField('Количество')
    price = models.DecimalField('Цена на момент заказа', max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'order_items'
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'
    
    def __str__(self):
        return f'{self.dish.name} x{self.quantity}'
    
    def get_total(self):
        """Сумма позиции заказа (цена * количество)"""
        return self.price * self.quantity