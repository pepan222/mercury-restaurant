from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
from django.contrib.sitemaps import views as sitemap_views
from django.urls import reverse

# Импорт моделей для sitemap
from menu.models import Dish, Category


class StaticViewSitemap:
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Список URL-имён для статических страниц
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


class DishSitemap:
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return Dish.objects.filter(is_available=True)

    def lastmod(self, obj):
        # Если у модели Dish есть поле updated_at, иначе вернёт None
        return getattr(obj, 'updated_at', None)


class CategorySitemap:
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Category.objects.all()


sitemaps = {
    'static': StaticViewSitemap,
    'dishes': DishSitemap,
    'categories': CategorySitemap,
}


urlpatterns = [
    path('dashboard/', include('dashboard.urls')),
    # path('admin/', admin_site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('core.urls')),
    path('menu/', include('menu.urls')),
    path('orders/', include('orders.urls')),
    path('bookings/', include('bookings.urls')),
    path('reviews/', include('reviews.urls')),
    path('accounts/', include('users.urls')),
    # Карта сайта
    path('sitemap.xml', sitemap_views.sitemap, {'sitemaps': sitemaps},
         name='django.contrib.sitemaps.views.sitemap'),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)