"""
Configuration des URLs principales
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

admin.site.site_header  = "🎓 Gestion des Présences"
admin.site.site_title   = "Présences Admin"
admin.site.index_title  = "Tableau de bord administrateur"

urlpatterns = [
    path('admin/',      admin.site.urls),
    path('auth/',       include('accounts.urls')),
    path('academic/',   include('academic.urls')),
    path('attendance/', include('attendance.urls')),
    path('dashboard/',  include('dashboard.urls')),
    path('',            include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )