from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import re
from .models import Profile
from orders.models import Order
from bookings.models import Reservation


def validate_password_strength(password):
    """
    Проверка сложности пароля:
    - минимум 8 символов
    - хотя бы одна заглавная буква (A-Z)
    - хотя бы одна строчная буква (a-z)
    - хотя бы одна цифра (0-9)
    - хотя бы один специальный символ
    """
    errors = []
    
    # Проверка длины
    if len(password) < 8:
        errors.append('Пароль должен содержать минимум 8 символов')
    
    # Проверка на заглавные буквы
    if not re.search(r'[A-Z]', password):
        errors.append('Пароль должен содержать хотя бы одну заглавную букву (A-Z)')
    
    # Проверка на строчные буквы
    if not re.search(r'[a-z]', password):
        errors.append('Пароль должен содержать хотя бы одну строчную букву (a-z)')
    
    # Проверка на цифры
    if not re.search(r'[0-9]', password):
        errors.append('Пароль должен содержать хотя бы одну цифру (0-9)')
    
    # Проверка на специальные символы
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>/?\\|`~]', password):
        errors.append('Пароль должен содержать хотя бы один специальный символ (!@#$%^&*()_+-= и т.д.)')
    
    return errors


def register(request):
    """Регистрация пользователя с проверкой сложности пароля"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        phone = request.POST.get('phone', '')
        
        errors = []
        
        # Проверка на пустые поля
        if not username:
            errors.append('Имя пользователя обязательно')
        if not email:
            errors.append('Email обязателен')
        if not password:
            errors.append('Пароль обязателен')
        
        # Проверка совпадения паролей
        if password and password2 and password != password2:
            errors.append('Пароли не совпадают')
        
        # Проверка существования пользователя
        if username and User.objects.filter(username=username).exists():
            errors.append('Пользователь с таким именем уже существует')
        
        # Проверка существования email
        if email and User.objects.filter(email=email).exists():
            errors.append('Пользователь с таким email уже существует')
        
        # Новая проверка сложности пароля
        if password:
            password_errors = validate_password_strength(password)
            errors.extend(password_errors)
        
        # Если есть ошибки, возвращаем JSON
        if errors:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'errors': errors
                }, status=400)
            for error in errors:
                messages.error(request, error)
            return redirect('users:register')
        
        # Создаем пользователя
        user = User.objects.create_user(username=username, email=email, password=password)
        Profile.objects.create(user=user, phone=phone)
        
        # Автоматически входим после регистрации
        login(request, user)
        
        # Если это AJAX-запрос
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Регистрация успешна! Добро пожаловать!',
                'redirect_url': '/'
            })
        
        messages.success(request, 'Регистрация успешна! Добро пожаловать!')
        return redirect('core:home')
    
    return render(request, 'registration/register.html')


def login_view(request):
    """Кастомный вход пользователя с поддержкой AJAX"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Проверка на пустые поля
        if not username or not password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Пожалуйста, заполните все поля'
                }, status=400)
            messages.error(request, 'Пожалуйста, заполните все поля')
            return redirect('users:login')
        
        # Аутентификация пользователя
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Если это AJAX-запрос
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': 'Вход выполнен успешно!',
                    'redirect_url': '/'
                })
            messages.success(request, 'Вход выполнен успешно!')
            return redirect('core:home')
        else:
            # Неверные учетные данные
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Неверное имя пользователя или пароль'
                }, status=400)
            messages.error(request, 'Неверное имя пользователя или пароль')
            return redirect('users:login')
    
    return render(request, 'registration/login.html')


@login_required
def profile(request):
    """Профиль пользователя"""
    # Получаем или создаем профиль пользователя
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Получаем заказы пользователя (последние 10)
    orders = Order.objects.filter(user=request.user).order_by('-order_date')[:10]
    
    # Получаем бронирования пользователя (последние 10)
    reservations = Reservation.objects.filter(user=request.user).order_by('-reservation_date', '-reservation_time')[:10]
    
    return render(request, 'users/profile.html', {
        'orders': orders,
        'reservations': reservations,
        'profile': profile,
    })

@login_required
def edit_profile(request):
    """Редактирование профиля"""
    # Получаем или создаем профиль пользователя
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        user = request.user
        
        # Обновляем данные пользователя
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.save()
        
        # Обновляем данные профиля
        profile.phone = request.POST.get('phone', '')
        profile.address = request.POST.get('address', '')
        profile.save()
        
        messages.success(request, 'Профиль успешно обновлен!')
        return redirect('users:profile')
    
    # Передаем данные в шаблон
    context = {
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'phone': profile.phone,
        'address': profile.address,
    }
    return render(request, 'users/edit_profile.html', context)