from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Главная
    path('', views.dashboard_index, name='index'),
    
    # Заказы
    path('orders/', views.dashboard_orders, name='orders'),
    path('orders/<int:order_id>/', views.dashboard_order_detail, name='order_detail'),
    path('orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    
    # Меню
    path('menu/', views.dashboard_menu, name='menu'),
    path('menu/add/', views.add_dish, name='add_dish'),
    path('menu/edit/<int:dish_id>/', views.edit_dish, name='edit_dish'),
    path('menu/delete/<int:dish_id>/', views.delete_dish, name='delete_dish'),
    path('menu/toggle/<int:dish_id>/', views.toggle_dish_availability, name='toggle_dish_availability'),
    
    # Категории 
    path('categories/', views.dashboard_categories, name='categories'),
    path('categories/add/', views.add_category, name='add_category'),
    path('categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    
    # Подкатегории 
    path('subcategories/', views.dashboard_subcategories, name='subcategories'),
    path('subcategories/add/', views.add_subcategory, name='add_subcategory'),
    path('subcategories/edit/<int:subcategory_id>/', views.edit_subcategory, name='edit_subcategory'),
    path('subcategories/delete/<int:subcategory_id>/', views.delete_subcategory, name='delete_subcategory'),
    
    # Столики
    path('tables/', views.dashboard_tables, name='tables'),
    path('tables/add/', views.add_table, name='add_table'),
    path('tables/edit/<int:table_id>/', views.edit_table, name='edit_table'),
    path('tables/delete/<int:table_id>/', views.delete_table, name='delete_table'),
    
    # Бронирования
    path('bookings/', views.dashboard_bookings, name='bookings'),
    path('bookings/add/', views.add_booking, name='add_booking'),
    path('bookings/update/<int:booking_id>/', views.update_booking_status, name='update_booking_status'),
    path('bookings/delete/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('api/available-tables/', views.get_available_tables_for_admin, name='api_available_tables'),
    
    # Отзывы
    path('reviews/', views.dashboard_reviews, name='reviews'),
    path('reviews/publish/<int:review_id>/', views.publish_review, name='publish_review'),
    path('reviews/delete/<int:review_id>/', views.delete_review, name='delete_review'),
]