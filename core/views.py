from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from menu.models import Category, Dish
from reviews.models import Review


def home(request):
    """Главная страница"""
    # Получаем 5 категорий для показа
    categories = Category.objects.all()[:5]
    
    # Получаем ОПУБЛИКОВАННЫЕ отзывы
    all_reviews = list(Review.objects.filter(is_published=True).order_by('-created_at'))
    
    # Популярные блюда
    featured_dishes = Dish.objects.filter(is_available=True).annotate(
        total_ordered=Sum('orderitem_set__quantity')
    ).order_by('-total_ordered', '-id')[:4]
    
    if not featured_dishes:
        featured_dishes = Dish.objects.filter(is_available=True)[:4]
    
    context = {
        'categories': categories,
        'reviews': all_reviews,
        'featured_dishes': featured_dishes,
    }
    return render(request, 'core/index.html', context)


def gallery(request):
    """Страница галереи"""
    return render(request, 'core/gallery.html')


def contacts(request):
    """Страница контактов"""
    return render(request, 'core/contacts.html')

def privacy_policy(request):
    """Страница политики конфиденциальности"""
    return render(request, 'privacy-policy.html')


# def menu_page(request):
#     """Страница меню"""
#     # Убираем filter(is_active=True) - такого поля нет в модели
#     # Просто получаем все категории
#     # categories = Category.objects.all()
#     # context = {
#     #     'categories': categories,
#     # }
    # return render(request, 'menu/menu_list.html')


# def booking_page(request):
#     """Страница бронирования"""
#     return render(request, 'bookings/booking.html')


# def cart_page(request):
#     """Страница корзины"""
#     return render(request, 'orders/cart.html')


@login_required
def create_review_ajax(request):
    """Создание отзыва через AJAX - БЕЗ МОДЕРАЦИИ, сразу публикуется"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        if not rating or not comment:
            return JsonResponse({'status': 'error', 'message': 'Заполните все поля'})
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return JsonResponse({'status': 'error', 'message': 'Оценка должна быть от 1 до 5'})
            
            review = Review.objects.create(
                user=request.user,
                rating=rating,
                comment=comment,
                is_published=True,
                is_moderated=True
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Спасибо за отзыв!',
                'review': {
                    'username': request.user.get_full_name() or request.user.username,
                    'rating': rating,
                    'comment': comment,
                    'created_at': review.created_at.strftime('%d.%m.%Y')
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Ошибка при сохранении отзыва'})
    
    return JsonResponse({'status': 'error', 'message': 'Неверный запрос'}, status=400)