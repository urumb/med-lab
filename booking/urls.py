"""
URL configuration for booking app
"""
from django.urls import path
from . import views

app_name = 'booking'  # IMPORTANT

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('book/', views.book_test, name='book_test'),
    path('book/<int:test_id>/', views.book_test, name='book_specific_test'),
    path('success/<int:booking_id>/', views.booking_success, name='booking_success'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),

    # Test related
    path('test/<int:test_id>/', views.test_detail, name='test_detail'),

    # Information pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),

    # AJAX/API endpoints
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/tests/', views.api_tests, name='api_tests'),
    path('api/quick-booking/', views.api_quick_booking, name='api_quick_booking'),

    # Admin dashboard
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
]
