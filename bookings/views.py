from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Table, Reservation


def is_time_valid_for_date(reservation_date, reservation_time):
    """Проверяет, что выбранное время не прошедшее для указанной даты"""
    try:
        # Объединяем дату и время в один datetime объект
        selected_datetime = datetime.strptime(f"{reservation_date} {reservation_time}", '%Y-%m-%d %H:%M')
        now = timezone.now()
        
        # Если дата сегодня, проверяем что время не прошедшее
        if selected_datetime.date() == now.date():
            return selected_datetime.time() > now.time()
        
        # Если дата в будущем, любое время допустимо
        return selected_datetime > now
    except (ValueError, TypeError):
        return False


@login_required
def booking_view(request):
    """Страница бронирования"""
    all_tables = Table.objects.filter(is_active=True)
    
    reservation_date = request.GET.get('reservation_date')
    reservation_time = request.GET.get('reservation_time')
    guest_count = request.GET.get('guest_count')
    
    if reservation_date and reservation_time:
        busy_table_ids = get_busy_tables(reservation_date, reservation_time)
        
        # Фильтруем по доступности и по количеству мест
        available_tables = all_tables.exclude(id__in=busy_table_ids)
        
        # Если указано количество гостей, фильтруем по вместимости
        if guest_count:
            try:
                guest_count_int = int(guest_count)
                available_tables = available_tables.filter(seats__gte=guest_count_int)
            except ValueError:
                pass
    else:
        available_tables = all_tables
    
    context = {
        'tables': available_tables,
        'selected_date': reservation_date or timezone.now().date().strftime('%Y-%m-%d'),
        'selected_time': reservation_time or '19:00',
        'selected_guests': reservation_date or '2',
    }
    return render(request, 'bookings/booking.html', context)


def get_busy_tables(reservation_date, reservation_time):
    """Получение ID занятых столов с учетом 2-часового интервала"""
    try:
        booking_time = datetime.strptime(reservation_time, '%H:%M').time()
    except ValueError:
        return []
    
    # Учитываем только активные бронирования (ожидание и подтверждено)
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


@login_required
def get_available_tables(request):
    """API для получения доступных столов на выбранные дату, время и количество гостей"""
    reservation_date = request.GET.get('date')
    reservation_time = request.GET.get('time')
    guest_count = request.GET.get('guests', '1')
    
    if not reservation_date or not reservation_time:
        return JsonResponse({'error': 'Не указаны дата и время'}, status=400)
    
    all_tables = Table.objects.filter(is_active=True)
    
    # Фильтруем по вместимости
    try:
        guest_count_int = int(guest_count)
        all_tables = all_tables.filter(seats__gte=guest_count_int)
    except ValueError:
        pass
    
    # Получаем занятые столы с учетом 2-часового интервала
    busy_table_ids = get_busy_tables(reservation_date, reservation_time)
    
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


@login_required
def create_booking(request):
    """Создание бронирования"""
    if request.method == 'POST':
        # --- ПРОВЕРКА СОГЛАСИЯ НА ОБРАБОТКУ ПЕРСОНАЛЬНЫХ ДАННЫХ (152-ФЗ) ---
        if not request.POST.get('personal_data_consent'):
            messages.error(request, 'Необходимо дать согласие на обработку персональных данных')
            return redirect('bookings:booking')
        
        table_id = request.POST.get('table_id')
        reservation_date = request.POST.get('reservation_date')
        reservation_time = request.POST.get('reservation_time')
        guest_count = request.POST.get('guest_count')
        comment = request.POST.get('comment', '')
        phone = request.POST.get('phone', '')
        
        table = get_object_or_404(Table, id=table_id)
        
        # --- НОВАЯ ПРОВЕРКА: нельзя бронировать на прошедшее время ---
        if not is_time_valid_for_date(reservation_date, reservation_time):
            messages.error(request, '❌ Нельзя забронировать столик на прошедшее время. Пожалуйста, выберите время в будущем.')
            return redirect('bookings:booking')
        
        # Проверка на количество гостей
        try:
            guest_count_int = int(guest_count)
            if table.seats < guest_count_int:
                messages.error(request, f'Стол №{table.table_number} рассчитан максимум на {table.seats} человек')
                return redirect('bookings:booking')
        except ValueError:
            messages.error(request, 'Укажите корректное количество гостей')
            return redirect('bookings:booking')
        
        # Проверка на занятость стола с учетом 2-часового интервала
        busy_table_ids = get_busy_tables(reservation_date, reservation_time)
        
        if table.id in busy_table_ids:
            messages.error(request, '❌ Этот стол уже забронирован на выбранное время или на ближайшие 2 часа')
            return redirect('bookings:booking')
        
        # Обновляем телефон в профиле
        if phone and phone != request.user.profile.phone:
            profile = request.user.profile
            profile.phone = phone
            profile.save()
        
        reservation = Reservation.objects.create(
            user=request.user,
            table=table,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            guest_count=guest_count,
            comment=comment
        )
        
        messages.success(request, f'✅ Стол №{table.table_number} забронирован!')
        return redirect('users:profile')
    
    return redirect('bookings:booking')


@login_required
def cancel_booking(request, booking_id):
    """Отмена бронирования"""
    reservation = get_object_or_404(Reservation, id=booking_id, user=request.user)
    
    if reservation.status == 'pending':
        reservation_datetime = datetime.combine(
            reservation.reservation_date, 
            reservation.reservation_time
        )
        now = datetime.now()
        
        if reservation_datetime > now + timedelta(hours=2):
            reservation.status = 'cancelled'
            reservation.save()
            messages.success(request, '✅ Бронирование отменено')
        else:
            messages.error(request, '❌ Нельзя отменить бронирование менее чем за 2 часа до начала')
    else:
        messages.error(request, '❌ Нельзя отменить это бронирование')
    
    return redirect('users:profile')