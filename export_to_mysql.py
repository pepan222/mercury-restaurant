import os
import django
import sqlite3

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mercury_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import connection
from menu.models import Category, Dish
from bookings.models import Table, Reservation
from reviews.models import Review
from orders.models import Order, OrderItem

print("🔄 Начинаем перенос данных...")

# 1. Проверяем подключение к MySQL
try:
    connection.ensure_connection()
    print("✅ Подключение к MySQL успешно")
except Exception as e:
    print(f"❌ Ошибка подключения к MySQL: {e}")
    print("Проверьте настройки DATABASES в settings.py")
    exit()

# 2. Создаем таблицы в MySQL через миграции
print("\n📦 Создаем таблицы в MySQL...")
call_command('migrate', verbosity=0)

# 3. Подключаемся к SQLite
sqlite_path = os.path.join(os.path.dirname(__file__), 'db.sqlite3')
if not os.path.exists(sqlite_path):
    print(f"❌ Файл SQLite не найден: {sqlite_path}")
    print("Сначала создайте данные в SQLite или пропустите этот шаг")
    exit()

sqlite_conn = sqlite3.connect(sqlite_path)
sqlite_cursor = sqlite_conn.cursor()
print("✅ Подключение к SQLite успешно")

# 4. Переносим пользователей
print("\n👤 Переносим пользователей...")
sqlite_cursor.execute("SELECT id, username, password, email, first_name, last_name, is_staff, is_superuser, is_active, date_joined FROM auth_user")
users = sqlite_cursor.fetchall()

count = 0
for user in users:
    if not User.objects.filter(username=user[1]).exists():
        new_user = User.objects.create_user(
            username=user[1],
            email=user[3] or '',
            first_name=user[4] or '',
            last_name=user[5] or '',
        )
        new_user.password = user[2]
        new_user.is_staff = user[6]
        new_user.is_superuser = user[7]
        new_user.is_active = user[8]
        new_user.date_joined = user[9]
        new_user.save()
        count += 1
        print(f"  ✅ Пользователь: {user[1]}")

print(f"  📊 Перенесено пользователей: {count}")

# 5. Переносим категории
print("\n📂 Переносим категории...")
sqlite_cursor.execute("SELECT id, name, description, slug, `order` FROM menu_category")
categories = sqlite_cursor.fetchall()

count = 0
for cat in categories:
    if not Category.objects.filter(name=cat[1]).exists():
        Category.objects.create(
            name=cat[1],
            description=cat[2] or '',
            slug=cat[3],
            order=cat[4]
        )
        count += 1
        print(f"  ✅ Категория: {cat[1]}")

print(f"  📊 Перенесено категорий: {count}")

# 6. Переносим блюда
print("\n🍽️ Переносим блюда...")
sqlite_cursor.execute("SELECT id, category_id, name, description, price, weight, is_available, `order` FROM menu_dish")
dishes = sqlite_cursor.fetchall()

count = 0
for dish in dishes:
    try:
        category = Category.objects.get(id=dish[1])
        if not Dish.objects.filter(name=dish[2], category=category).exists():
            Dish.objects.create(
                category=category,
                name=dish[2],
                description=dish[3] or '',
                price=dish[4],
                weight=dish[5],
                is_available=dish[6],
                order=dish[7]
            )
            count += 1
            print(f"  ✅ Блюдо: {dish[2]}")
    except Category.DoesNotExist:
        print(f"  ⚠️ Категория для блюда {dish[2]} не найдена")

print(f"  📊 Перенесено блюд: {count}")

# 7. Переносим столы
print("\n🪑 Переносим столы...")
sqlite_cursor.execute("SELECT id, table_number, seats, location, is_active FROM bookings_table")
tables = sqlite_cursor.fetchall()

count = 0
for table in tables:
    if not Table.objects.filter(table_number=table[1]).exists():
        Table.objects.create(
            table_number=table[1],
            seats=table[2],
            location=table[3],
            is_active=table[4]
        )
        count += 1
        print(f"  ✅ Стол №{table[1]}")
    else:
        print(f"  ⚠️ Стол №{table[1]} уже существует")

print(f"  📊 Перенесено столов: {count}")

# 8. Переносим отзывы
print("\n⭐ Переносим отзывы...")
sqlite_cursor.execute("SELECT id, user_id, rating, comment, is_moderated, is_published, created_at FROM reviews_review")
reviews = sqlite_cursor.fetchall()

count = 0
for review in reviews:
    try:
        user = User.objects.get(id=review[1])
        if not Review.objects.filter(user=user, comment=review[3]).exists():
            Review.objects.create(
                user=user,
                rating=review[2],
                comment=review[3],
                is_moderated=review[4],
                is_published=review[5],
                created_at=review[6]
            )
            count += 1
            print(f"  ✅ Отзыв от {user.username}")
    except User.DoesNotExist:
        print(f"  ⚠️ Пользователь для отзыва не найден")

print(f"  📊 Перенесено отзывов: {count}")

# 9. Переносим заказы
print("\n📦 Переносим заказы...")
sqlite_cursor.execute("SELECT id, user_id, order_date, total_amount, delivery_cost, delivery_address, payment_method, status, comment FROM orders_order")
orders = sqlite_cursor.fetchall()

count = 0
for order in orders:
    try:
        user = User.objects.get(id=order[1])
        if not Order.objects.filter(user=user, order_date=order[2]).exists():
            new_order = Order.objects.create(
                user=user,
                order_date=order[2],
                total_amount=order[3],
                delivery_cost=order[4] or 0,
                delivery_address=order[5],
                payment_method=order[6],
                status=order[7],
                comment=order[8] or ''
            )
            count += 1
            print(f"  ✅ Заказ #{new_order.id} от {user.username}")
            
            # Переносим товары заказа
            sqlite_cursor.execute("SELECT dish_id, quantity, price FROM orders_orderitem WHERE order_id = ?", (order[0],))
            items = sqlite_cursor.fetchall()
            for item in items:
                try:
                    dish = Dish.objects.get(id=item[0])
                    OrderItem.objects.create(
                        order=new_order,
                        dish=dish,
                        quantity=item[1],
                        price=item[2]
                    )
                except Dish.DoesNotExist:
                    print(f"    ⚠️ Блюдо {item[0]} не найдено")
    except User.DoesNotExist:
        print(f"  ⚠️ Пользователь для заказа не найден")

print(f"  📊 Перенесено заказов: {count}")

# Закрываем соединение с SQLite
sqlite_conn.close()

print("\n🎉 Перенос данных завершен успешно!")
print("\n✅ Проверьте данные в админ-панели: http://127.0.0.1:8000/dashboard/")