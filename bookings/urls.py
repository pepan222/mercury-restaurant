from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.booking_view, name='booking'),
    path('create/', views.create_booking, name='create_booking'),
    path('cancel/<int:booking_id>/', views.cancel_booking, name='cancel_booking'),
    path('api/available-tables/', views.get_available_tables, name='api_available_tables'),
]