from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('gallery/', views.gallery, name='gallery'),
    path('contacts/', views.contacts, name='contacts'),
    # path('menu/', views.menu_page, name='menu_list'),
    # path('bookings/', views.booking_page, name='booking'),
    # path('orders/cart/', views.cart_page, name='cart'),
    path('reviews/create/', views.create_review_ajax, name='create_review_ajax'),
]