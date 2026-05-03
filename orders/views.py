from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from datetime import datetime
from .models import Cart, CartItem, Order, OrderItem
from menu.models import Dish
from users.models import Profile

@login_required
def cart_view(request):
    """Просмотр корзины"""
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    return render(request, 'orders/cart.html', {'cart': cart})

@login_required
def add_to_cart(request, dish_id):
    """Добавление в корзину"""
    dish = get_object_or_404(Dish, id=dish_id)
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    
    quantity = int(request.GET.get('quantity', 1))
    
    cart_item, created = CartItem.objects.get_or_create(cart=cart, dish=dish)
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    else:
        cart_item.quantity = quantity
        cart_item.save()
    
    total_items = sum(item.quantity for item in cart.items.all())
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'cart_count': total_items,
            'message': f'{dish.name} добавлен в корзину'
        })
    
    messages.success(request, f'{dish.name} добавлен в корзину')
    return redirect('orders:cart')

@login_required
def remove_from_cart(request, item_id):
    """Удаление из корзины"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        cart_item.delete()
        
        # Подсчитываем общее количество товаров в корзине
        cart = Cart.objects.filter(user=request.user, is_active=True).first()
        total_items = sum(item.quantity for item in cart.items.all()) if cart else 0
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'cart_count': total_items,
                'message': 'Товар удален из корзины'
            })
        
        messages.success(request, 'Товар удален из корзины')
        return redirect('orders:cart')
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        messages.error(request, 'Ошибка при удалении товара')
        return redirect('orders:cart')

@login_required
@csrf_protect
@require_http_methods(["POST"])
def update_cart_item(request, item_id):
    """Обновление количества"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart_item.delete()
            return JsonResponse({
                'status': 'deleted',
                'message': 'Товар удален'
            })
        
        cart = cart_item.cart
        total = cart.get_total()
        delivery_cost = 200 if total < 1500 else 0
        
        return JsonResponse({
            'status': 'success',
            'new_quantity': cart_item.quantity,
            'item_total': float(cart_item.get_total()),
            'cart_total': float(total),
            'delivery_cost': delivery_cost,
            'final_total': float(total + delivery_cost)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

def is_delivery_available():
    """Проверяет, доступна ли доставка в текущее время (с 12:00 до 21:00)"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    current_time_in_minutes = current_hour * 60 + current_minute
    
    start_time = 12 * 60      # 12:00
    end_time = 21 * 60        # 21:00
    
    return start_time <= current_time_in_minutes < end_time

@login_required
def checkout(request):
    """Оформление заказа"""
    cart = Cart.objects.filter(user=request.user, is_active=True).first()
    if not cart or not cart.items.exists():
        messages.error(request, 'Корзина пуста')
        return redirect('menu:menu_list')
    
    # Проверяем, доступна ли доставка по времени
    delivery_available = is_delivery_available()
    
    # Получаем профиль пользователя для подтягивания адреса
    profile, created = Profile.objects.get_or_create(user=request.user)
    user_address = profile.address or ''
    
    if request.method == 'POST':
        # --- ПРОВЕРКА СОГЛАСИЯ НА ОБРАБОТКУ ПЕРСОНАЛЬНЫХ ДАННЫХ (152-ФЗ) ---
        if not request.POST.get('personal_data_consent'):
            messages.error(request, 'Для оформления заказа необходимо дать согласие на обработку персональных данных')
            return redirect('orders:checkout')
        
        # Если доставка недоступна, показываем ошибку и перенаправляем обратно
        if not delivery_available:
            messages.error(request, 'Доставка работает с 12:00 до 21:00. Пожалуйста, оформите заказ в рабочее время.')
            return redirect('orders:checkout')
        
        # Рассчитываем стоимость доставки
        delivery_cost = 200 if cart.get_total() < 1500 else 0
        cart_total = cart.get_total()
        total_with_delivery = cart_total + delivery_cost
        
        # Получаем адрес из формы
        address = request.POST.get('address', '')
        
        address_parts = [
            address,
            request.POST.get('entrance', ''),
            request.POST.get('floor', ''),
            request.POST.get('intercom', '')
        ]
        full_address = ', '.join([p for p in address_parts if p])
        
        order = Order.objects.create(
            user=request.user,
            delivery_address=full_address,
            payment_method=request.POST.get('payment_method'),
            comment=request.POST.get('comment', ''),
            delivery_cost=delivery_cost
        )
        
        total = 0
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                dish=item.dish,
                quantity=item.quantity,
                price=item.dish.price
            )
            total += item.dish.price * item.quantity
        
        # Сохраняем полную сумму с доставкой
        order.total_amount = total_with_delivery
        order.save()
        
        cart.is_active = False
        cart.save()
        
        return redirect('orders:order_success', order_id=order.id)
    
    # GET-запрос — показываем страницу оформления
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'user_address': user_address,
        'is_delivery_available': delivery_available,
    })

@login_required
def order_success(request, order_id):
    """Страница успешного заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})

@login_required
def my_orders(request):
    """Мои заказы"""
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    return render(request, 'orders/my_orders.html', {'orders': orders})

@login_required
def api_cart_count(request):
    """API для получения количества товаров в корзине (НЕ сумма, а количество)"""
    cart, created = Cart.objects.get_or_create(user=request.user, is_active=True)
    total_items = sum(item.quantity for item in cart.items.all())
    return JsonResponse({'count': total_items})