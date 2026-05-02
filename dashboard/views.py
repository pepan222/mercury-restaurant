from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from django.urls import reverse
from django.http import JsonResponse
from orders.models import Order
from bookings.models import Reservation, Table
from reviews.models import Review
from menu.models import Category, Dish, Subcategory
from django.contrib.auth.models import User
from users.models import Profile


@staff_member_required
def dashboard_index(request):
    """Главная страница админ-панели"""
    today = timezone.now().date()
    
    total_orders = Order.objects.count()
    today_orders = Order.objects.filter(order_date__date=today).count()
    pending_orders = Order.objects.filter(status='pending').count()
    
    total_revenue = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    today_revenue = Order.objects.filter(order_date__date=today).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    total_reservations = Reservation.objects.count()
    today_reservations = Reservation.objects.filter(reservation_date=today).count()
    
    pending_reviews = Review.objects.filter(is_published=False).count()
    pending_reviews_list = Review.objects.filter(is_published=False)[:5]
    
    recent_orders = Order.objects.order_by('-order_date')[:10]
    recent_reservations = Reservation.objects.order_by('-created_at')[:10]
    
    context = {
        'total_orders': total_orders,
        'today_orders': today_orders,
        'pending_orders': pending_orders,
        'total_revenue': total_revenue,
        'today_revenue': today_revenue,
        'total_reservations': total_reservations,
        'today_reservations': today_reservations,
        'pending_reviews': pending_reviews,
        'pending_reviews_list': pending_reviews_list,
        'recent_orders': recent_orders,
        'recent_reservations': recent_reservations,
        'now': timezone.now(),
        'active': 'index',
    }
    return render(request, 'dashboard/index.html', context)


@staff_member_required
def dashboard_orders(request):
    """Управление заказами"""
    orders = Order.objects.all().order_by('-order_date')
    return render(request, 'dashboard/orders.html', {
        'orders': orders,
        'active': 'orders',
    })


@staff_member_required
def dashboard_order_detail(request, order_id):
    """Детали заказа"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Статус заказа #{order.id} изменен на "{order.get_status_display()}"')
        return redirect('dashboard:order_detail', order_id=order.id)
    
    return render(request, 'dashboard/order_detail.html', {
        'order': order,
        'active': 'orders',
    })


@staff_member_required
def update_order_status(request, order_id):
    """Обновление статуса заказа (для быстрого переключения)"""
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Статус заказа #{order.id} изменен')
        else:
            messages.error(request, 'Неверный статус')
    return redirect('dashboard:orders')


@staff_member_required
def dashboard_menu(request):
    """Управление меню"""
    categories = Category.objects.prefetch_related('subcategories', 'dishes').all()
    return render(request, 'dashboard/menu.html', {
        'categories': categories,
        'active': 'menu',
    })


@staff_member_required
def toggle_dish_availability(request, dish_id):
    """Включить/выключить доступность блюда"""
    dish = get_object_or_404(Dish, id=dish_id)
    dish.is_available = not dish.is_available
    dish.save()
    status = "доступно" if dish.is_available else "недоступно"
    messages.success(request, f'Блюдо "{dish.name}" теперь {status}')
    return redirect(f"{reverse('dashboard:menu')}#dish-{dish_id}")


@staff_member_required
def add_dish(request):
    """Добавление нового блюда"""
    categories = Category.objects.all()
    subcategories = Subcategory.objects.all()
    
    pre_selected_category = request.GET.get('category_id')
    
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        subcategory_id = request.POST.get('subcategory_id')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        weight = request.POST.get('weight', None)
        image = request.FILES.get('image')
        
        if not category_id or not name or not price:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('dashboard:add_dish')
        
        try:
            category = Category.objects.get(id=category_id)
            subcategory = None
            if subcategory_id:
                subcategory = Subcategory.objects.get(id=subcategory_id)
            
            dish = Dish.objects.create(
                category=category,
                subcategory=subcategory,
                name=name,
                description=description,
                price=price,
                weight=weight if weight else None,
                is_available=True,
                image=image
            )
            messages.success(request, f'Блюдо "{name}" добавлено')
            return redirect(f"{reverse('dashboard:menu')}#category-{category.id}")
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении: {e}')
    
    return render(request, 'dashboard/add_dish.html', {
        'categories': categories,
        'subcategories': subcategories,
        'pre_selected_category': pre_selected_category,
        'active': 'menu',
    })


@staff_member_required
def edit_dish(request, dish_id):
    """Редактирование блюда"""
    dish = get_object_or_404(Dish, id=dish_id)
    categories = Category.objects.all()
    subcategories = Subcategory.objects.filter(category=dish.category)
    
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        subcategory_id = request.POST.get('subcategory_id')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        weight = request.POST.get('weight', None)
        is_available = request.POST.get('is_available') == 'on'
        image = request.FILES.get('image')
        
        if not category_id or not name or not price:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('dashboard:edit_dish', dish_id=dish_id)
        
        try:
            category = Category.objects.get(id=category_id)
            subcategory = None
            if subcategory_id:
                subcategory = Subcategory.objects.get(id=subcategory_id)
            
            dish.category = category
            dish.subcategory = subcategory
            dish.name = name
            dish.description = description
            dish.price = price
            dish.weight = weight if weight else None
            dish.is_available = is_available
            
            if image:
                dish.image = image
            
            dish.save()
            messages.success(request, f'Блюдо "{name}" обновлено')
            return redirect(f"{reverse('dashboard:menu')}#dish-{dish.id}")
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении: {e}')
    
    return render(request, 'dashboard/edit_dish.html', {
        'dish': dish,
        'categories': categories,
        'subcategories': subcategories,
        'active': 'menu',
    })


@staff_member_required
def delete_dish(request, dish_id):
    """Удаление блюда"""
    dish = get_object_or_404(Dish, id=dish_id)
    dish_name = dish.name
    
    category_id = request.GET.get('category_id')
    if not category_id:
        category_id = dish.category.id
    
    dish.delete()
    messages.success(request, f'Блюдо "{dish_name}" удалено')
    return redirect(f"{reverse('dashboard:menu')}#category-{category_id}")


# ========== УПРАВЛЕНИЕ СТОЛИКАМИ ==========

@staff_member_required
def dashboard_tables(request):
    """Управление столиками"""
    tables = Table.objects.all().order_by('table_number')
    return render(request, 'dashboard/tables.html', {
        'tables': tables,
        'active': 'tables',
    })


@staff_member_required
def add_table(request):
    """Добавление нового столика"""
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        seats = request.POST.get('seats')
        location = request.POST.get('location')
        is_active = request.POST.get('is_active') == 'on'
        
        if not table_number or not seats:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('dashboard:add_table')
        
        if Table.objects.filter(table_number=table_number).exists():
            messages.error(request, f'Стол с номером {table_number} уже существует')
            return redirect('dashboard:add_table')
        
        try:
            Table.objects.create(
                table_number=table_number,
                seats=seats,
                location=location,
                is_active=is_active
            )
            messages.success(request, f'Стол №{table_number} добавлен')
            return redirect('dashboard:tables')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении: {e}')
    
    return render(request, 'dashboard/add_table.html', {
        'active': 'tables',
    })


@staff_member_required
def edit_table(request, table_id):
    """Редактирование столика"""
    table = get_object_or_404(Table, id=table_id)
    
    if request.method == 'POST':
        table_number = request.POST.get('table_number')
        seats = request.POST.get('seats')
        location = request.POST.get('location')
        is_active = request.POST.get('is_active') == 'on'
        
        if not table_number or not seats:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('dashboard:edit_table', table_id=table_id)
        
        if Table.objects.filter(table_number=table_number).exclude(id=table.id).exists():
            messages.error(request, f'Стол с номером {table_number} уже существует')
            return redirect('dashboard:edit_table', table_id=table_id)
        
        try:
            table.table_number = table_number
            table.seats = seats
            table.location = location
            table.is_active = is_active
            table.save()
            messages.success(request, f'Стол №{table_number} обновлен')
            return redirect('dashboard:tables')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении: {e}')
    
    return render(request, 'dashboard/edit_table.html', {
        'table': table,
        'active': 'tables',
    })


@staff_member_required
def delete_table(request, table_id):
    """Удаление столика"""
    table = get_object_or_404(Table, id=table_id)
    table_number = table.table_number
    
    future_reservations = Reservation.objects.filter(
        table=table,
        reservation_date__gte=timezone.now().date(),
        status__in=['pending', 'confirmed']
    ).exists()
    
    if future_reservations:
        messages.error(request, f'Нельзя удалить стол №{table_number}, так как на него есть будущие бронирования')
    else:
        table.delete()
        messages.success(request, f'Стол №{table_number} удален')
    
    return redirect('dashboard:tables')


# ========== УПРАВЛЕНИЕ БРОНИРОВАНИЯМИ ==========

@staff_member_required
def dashboard_bookings(request):
    """Управление бронированиями"""
    bookings = Reservation.objects.select_related('user', 'table').all().order_by('-reservation_date', 'reservation_time')
    return render(request, 'dashboard/bookings.html', {
        'bookings': bookings,
        'active': 'bookings',
    })


@staff_member_required
def get_available_tables_for_admin(request):
    """API для получения доступных столов для администратора"""
    reservation_date = request.GET.get('date')
    reservation_time = request.GET.get('time')
    guest_count = request.GET.get('guests', '1')
    
    if not reservation_date or not reservation_time:
        return JsonResponse({'error': 'Не указаны дата и время'}, status=400)
    
    # Получаем все активные столы
    all_tables = Table.objects.filter(is_active=True)
    
    # Фильтруем по количеству гостей
    try:
        guest_count_int = int(guest_count)
        all_tables = all_tables.filter(seats__gte=guest_count_int)
    except ValueError:
        pass
    
    # Получаем занятые столы con учетом 2-часового интервала
    busy_table_ids = get_busy_tables_for_admin(reservation_date, reservation_time)
    available_tables = all_tables.exclude(id__in=busy_table_ids)
    
    tables_data = []
    for table in available_tables:
        tables_data.append({
            'id': table.id,
            'number': table.table_number,
            'seats': table.seats,
            'location': table.location,
        })
    
    return JsonResponse({'tables': tables_data})


def get_busy_tables_for_admin(reservation_date, reservation_time):
    """Получение ID занятых столов для админки с учетом 2-часового интервала"""
    try:
        booking_time = datetime.strptime(reservation_time, '%H:%M').time()
    except ValueError:
        return []
    
    reservations = Reservation.objects.filter(
        reservation_date=reservation_date,
        status__in=['pending', 'confirmed']
    )
    
    busy_table_ids = set()
    
    for reservation in reservations:
        res_time = reservation.reservation_time
        res_datetime = datetime.combine(datetime.today().date(), res_time)
        end_datetime = res_datetime + timedelta(hours=2)
        end_time = end_datetime.time()
        
        if res_time <= booking_time < end_time:
            busy_table_ids.add(reservation.table_id)
    
    return list(busy_table_ids)


def is_table_busy_for_admin(table_id, reservation_date, reservation_time):
    """Проверка, занят ли стол с учетом 2-часового интервала"""
    try:
        booking_time = datetime.strptime(reservation_time, '%H:%M').time()
    except ValueError:
        return True
    
    reservations = Reservation.objects.filter(
        table_id=table_id,
        reservation_date=reservation_date,
        status__in=['pending', 'confirmed']
    )
    
    for res in reservations:
        res_time = res.reservation_time
        res_datetime = datetime.combine(datetime.today().date(), res_time)
        end_datetime = res_datetime + timedelta(hours=2)
        end_time = end_datetime.time()
        
        if res_time <= booking_time < end_time:
            return True
    
    return False


@staff_member_required
def add_booking(request):
    """Добавление очного бронирования"""
    tables = Table.objects.filter(is_active=True).order_by('table_number')
    
    # Получаем или создаем пользователя "Очный клиент"
    offline_client, created = User.objects.get_or_create(
        username='offline_client',
        defaults={
            'email': 'offline@mercury.ru',
            'first_name': 'Очный',
            'last_name': 'клиент'
        }
    )
    if created:
        offline_client.set_password('offline_client_2024')
        offline_client.save()
        Profile.objects.get_or_create(user=offline_client, defaults={'phone': 'Не указан'})
    
    # Получаем текущее время в локальном часовом поясе
    now = timezone.localtime(timezone.now())
    current_time = now.time()
    
    # Форматируем текущее время
    default_time = current_time.strftime('%H:%M')
    
    if request.method == 'POST':
        table_id = request.POST.get('table_id')
        reservation_date = request.POST.get('reservation_date')
        reservation_time = request.POST.get('reservation_time')
        guest_count = request.POST.get('guest_count')
        status = request.POST.get('status')
        comment = request.POST.get('comment', '')
        
        if not table_id or not reservation_date or not reservation_time or not guest_count:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('dashboard:add_booking')
        
        table = get_object_or_404(Table, id=table_id)
        
        # Проверка на количество гостей
        try:
            guest_count_int = int(guest_count)
            if table.seats < guest_count_int:
                messages.error(request, f'Стол №{table.table_number} рассчитан максимум на {table.seats} человек')
                return redirect('dashboard:add_booking')
        except ValueError:
            messages.error(request, 'Укажите корректное количество гостей')
            return redirect('dashboard:add_booking')
        
        # Проверка на занятость стола с учетом 2-часового интервала
        if is_table_busy_for_admin(table.id, reservation_date, reservation_time):
            messages.error(request, f'Стол №{table.table_number} уже забронирован на это время или на ближайшие 2 часа')
            return redirect('dashboard:add_booking')
        
        try:
            # Создаем бронирование для очного клиента
            reservation = Reservation.objects.create(
                user=offline_client,
                table=table,
                reservation_date=reservation_date,
                reservation_time=reservation_time,
                guest_count=guest_count,
                status=status,
                comment=comment
            )
            messages.success(request, f'Бронирование стола №{table.table_number} для очного клиента на {reservation_date} {reservation_time} создано')
            return redirect('dashboard:bookings')
        except Exception as e:
            messages.error(request, f'Ошибка при создании бронирования: {e}')
    
    context = {
        'tables': tables,
        'active': 'bookings',
        'today': timezone.localtime(timezone.now()).date().strftime('%Y-%m-%d'),
        'default_time': default_time,
    }
    return render(request, 'dashboard/add_booking.html', context)


@staff_member_required
def update_booking_status(request, booking_id):
    """Обновление статуса бронирования"""
    booking = get_object_or_404(Reservation, id=booking_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Reservation.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            messages.success(request, f'Статус бронирования #{booking.id} изменен на "{booking.get_status_display()}"')
        else:
            messages.error(request, 'Неверный статус')
    return redirect('dashboard:bookings')


@staff_member_required
def delete_booking(request, booking_id):
    """Удаление (отмена) бронирования"""
    booking = get_object_or_404(Reservation, id=booking_id)
    booking.status = 'cancelled'
    booking.save()
    messages.success(request, f'Бронирование #{booking.id} отменено')
    return redirect('dashboard:bookings')


@staff_member_required
def dashboard_reviews(request):
    """Модерация отзывов"""
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'dashboard/reviews.html', {
        'reviews': reviews,
        'active': 'reviews',
    })


@staff_member_required
def publish_review(request, review_id):
    """Публикация отзыва"""
    review = get_object_or_404(Review, id=review_id)
    review.is_published = True
    review.is_moderated = True
    review.save()
    messages.success(request, 'Отзыв опубликован')
    return redirect('dashboard:reviews')


@staff_member_required
def delete_review(request, review_id):
    """Удаление отзыва"""
    review = get_object_or_404(Review, id=review_id)
    review.delete()
    messages.success(request, 'Отзыв удален')
    return redirect('dashboard:reviews')


# ========== УПРАВЛЕНИЕ КАТЕГОРИЯМИ ==========

@staff_member_required
def dashboard_categories(request):
    """Управление категориями"""
    categories = Category.objects.all().order_by('order')
    return render(request, 'dashboard/categories.html', {
        'categories': categories,
        'active': 'categories',
    })


@staff_member_required
def add_category(request):
    """Добавление новой категории"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        order = request.POST.get('order', 0)
        
        if not name:
            messages.error(request, 'Введите название категории')
            return redirect('dashboard:add_category')
        
        try:
            Category.objects.create(
                name=name,
                description=description,
                order=order
            )
            messages.success(request, f'Категория "{name}" добавлена')
            return redirect('dashboard:categories')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении: {e}')
    
    return render(request, 'dashboard/add_category.html', {
        'active': 'categories',
    })


@staff_member_required
def edit_category(request, category_id):
    """Редактирование категории"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        order = request.POST.get('order', 0)
        
        if not name:
            messages.error(request, 'Введите название категории')
            return redirect('dashboard:edit_category', category_id=category_id)
        
        try:
            category.name = name
            category.description = description
            category.order = order
            category.save()
            messages.success(request, f'Категория "{name}" обновлена')
            return redirect('dashboard:categories')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении: {e}')
    
    return render(request, 'dashboard/edit_category.html', {
        'category': category,
        'active': 'categories',
    })


@staff_member_required
def delete_category(request, category_id):
    """Удаление категории"""
    category = get_object_or_404(Category, id=category_id)
    category_name = category.name
    
    if category.dishes.exists():
        messages.error(request, f'Нельзя удалить категорию "{category_name}", так как в ней есть блюда')
    else:
        category.delete()
        messages.success(request, f'Категория "{category_name}" удалена')
    
    return redirect('dashboard:categories')


# ========== УПРАВЛЕНИЕ ПОДКАТЕГОРИЯМИ ==========

@staff_member_required
def dashboard_subcategories(request):
    """Управление подкатегориями"""
    subcategories = Subcategory.objects.select_related('category').all().order_by('category__order', 'order')
    return render(request, 'dashboard/subcategories.html', {
        'subcategories': subcategories,
        'active': 'subcategories',
    })


@staff_member_required
def add_subcategory(request):
    """Добавление новой подкатегории"""
    categories = Category.objects.all().order_by('order')
    
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        name = request.POST.get('name')
        order = request.POST.get('order', 0)
        
        if not category_id or not name:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('dashboard:add_subcategory')
        
        try:
            category = Category.objects.get(id=category_id)
            Subcategory.objects.create(
                category=category,
                name=name,
                order=order
            )
            messages.success(request, f'Подкатегория "{name}" добавлена')
            return redirect('dashboard:subcategories')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении: {e}')
    
    return render(request, 'dashboard/add_subcategory.html', {
        'categories': categories,
        'active': 'subcategories',
    })


@staff_member_required
def edit_subcategory(request, subcategory_id):
    """Редактирование подкатегории"""
    subcategory = get_object_or_404(Subcategory, id=subcategory_id)
    categories = Category.objects.all().order_by('order')
    
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        name = request.POST.get('name')
        order = request.POST.get('order', 0)
        
        if not category_id or not name:
            messages.error(request, 'Заполните все обязательные поля')
            return redirect('dashboard:edit_subcategory', subcategory_id=subcategory_id)
        
        try:
            category = Category.objects.get(id=category_id)
            subcategory.category = category
            subcategory.name = name
            subcategory.order = order
            subcategory.save()
            messages.success(request, f'Подкатегория "{name}" обновлена')
            return redirect('dashboard:subcategories')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении: {e}')
    
    return render(request, 'dashboard/edit_subcategory.html', {
        'subcategory': subcategory,
        'categories': categories,
        'active': 'subcategories',
    })


@staff_member_required
def delete_subcategory(request, subcategory_id):
    """Удаление подкатегории"""
    subcategory = get_object_or_404(Subcategory, id=subcategory_id)
    subcategory_name = subcategory.name
    
    if subcategory.dishes.exists():
        messages.error(request, f'Нельзя удалить подкатегорию "{subcategory_name}", так как в ней есть блюда')
    else:
        subcategory.delete()
        messages.success(request, f'Подкатегория "{subcategory_name}" удалена')
    
    return redirect('dashboard:subcategories')