from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps.views import sitemap as sitemap_view
from menu.models import Dish


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return [
            'core:home',
            'menu:menu_list',
            'core:gallery',
            'core:contacts',
            'bookings:booking',
            'orders:cart'
        ]

    def location(self, item):
        return reverse(item)


class DishSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Dish.objects.filter(is_available=True)

    # Если у модели Dish нет метода get_absolute_url, нужно указать location явно
    def location(self, obj):
        # Предположим, что у вас есть URL-имя 'menu:dish_detail' и используется pk или slug
        # Замените 'menu:dish_detail' на актуальное имя URL для детальной страницы блюда
        # Если такой страницы нет, то sitemap для блюд не нужен
        return reverse('menu:dish_detail', args=[obj.id])


sitemaps = {
    'static': StaticViewSitemap,
    'dishes': DishSitemap,
}

urlpatterns = [
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
    path('menu/', include('menu.urls')),
    path('orders/', include('orders.urls')),
    path('bookings/', include('bookings.urls')),
    path('reviews/', include('reviews.urls')),
    path('accounts/', include('users.urls')),
    path('sitemap.xml', sitemap_view, {'sitemaps': sitemaps}, name='sitemap'),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)