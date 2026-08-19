"""
URL configuration for booking app
"""
from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    # Main & Catalog
    path('', views.home, name='home'),
    path('tests/', views.test_catalog, name='test_catalog'),
    path('test/<int:test_id>/', views.test_detail, name='test_detail'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Patient Dashboard & Profile
    path('dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('profile/', views.patient_profile, name='patient_profile'),

    # Booking Workflow
    path('book/', views.book_test, name='book_test'),
    path('book/<int:test_id>/', views.book_test, name='book_specific_test'),
    path('success/<str:reference_number>/', views.booking_success, name='booking_success'),
    path('booking/<str:reference_number>/', views.booking_detail, name='booking_detail'),
    path('booking/<str:reference_number>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),

    # Admin Management Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/status-update/<int:booking_id>/', views.update_booking_status, name='update_booking_status'),

    # Static Pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),

    # AJAX & API Endpoints
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/tests/', views.api_tests, name='api_tests'),
]
