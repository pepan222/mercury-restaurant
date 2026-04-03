# 🍽️ Ресторан "Меркурий"

Сайт ресторана пяти кухонь в Батайске. Проект разработан на Django с адаптивным дизайном под все устройства.

![Django](https://img.shields.io/badge/Django-6.0.3-green)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 О проекте

Веб-сайт для ресторана "Меркурий", который представляет:

- 🍜 **5 кухонь мира** (Русская, Итальянская, Японская, Европейская, Кавказская)
- 📅 **Онлайн-бронирование** столиков
- 📖 **Меню** с категориями и подкатегориями
- 🛒 **Корзина заказов** с добавлением блюд
- ⭐ **Отзывы гостей** с рейтингом
- 🖼️ **Галерея** ресторана
- 📱 **Адаптивный дизайн** (Mobile First подход)

## 🛠️ Технологии

### Backend
- **Django 6.0.3** - основной фреймворк
- **MySQL** - база данных
- **django-crispy-forms** - стилизация форм
- **crispy-bootstrap5** - Bootstrap 5 интеграция

### Frontend
- **HTML5** - структура страниц
- **CSS3** - стилизация (адаптивный дизайн)
- **JavaScript** - интерактивность (слайдер, карусель, модальные окна)

### Дополнительно
- **Pillow** - работа с изображениями
- **python-dotenv** - управление переменными окружения

## 🚀 Установка и запуск

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/pepan222/mercury-restaurant.git
cd mercury-restaurant
```

### 2. Создайте виртуальное окружение
```bash
python -m venv venv
```

**Активируйте окружение:**
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 3. Установите зависимости
```bash
pip install -r requirements.txt
```

### 4. Настройте базу данных MySQL
```sql
CREATE DATABASE restaurant_mercury;
```

### 5. Настройте переменные окружения
Создайте файл `.env` в корне проекта:
```env
SECRET_KEY=ваш_секретный_ключ
DB_NAME=restaurant_mercury
DB_USER=root
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=3306
```

### 6. Примените миграции
```bash
python manage.py migrate
```

### 7. Создайте суперпользователя
```bash
python manage.py createsuperuser
```

### 8. Запустите сервер
```bash
python manage.py runserver
```

Сайт будет доступен по адресу: `http://127.0.0.1:8000`