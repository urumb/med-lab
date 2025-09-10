"""
URL configuration for medical_lab_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Customize admin site headers
admin.site.site_header = 'Medical Lab Management System'
admin.site.site_title = 'Medical Lab Admin'
admin.site.index_title = 'Welcome to Medical Lab Management'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('booking.urls')),  # Include booking app routes
]

# Serve media & static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
