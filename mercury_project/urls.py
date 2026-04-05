from django.urls import path, include, reverse
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.urls import re_path
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps.views import sitemap as sitemap_view


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Проверьте, что все эти URL-имена существуют
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


sitemaps = {
    'static': StaticViewSitemap,
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