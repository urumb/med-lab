"""
Views for the Medical Lab Booking System
"""
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import Category, Test, Patient, Booking
from .forms import (
    CombinedBookingForm,
    PatientForm,
    BookingForm,
    PatientRegisterForm,
    PatientProfileForm
)


def home(request):
    """Homepage showcasing medical lab features and categories"""
    categories = Category.objects.all().prefetch_related('tests')
    popular_tests = Test.objects.filter(is_active=True).order_by('-created_at')[:6]

    context = {
        'categories': categories,
        'popular_tests': popular_tests,
        'total_tests': Test.objects.filter(is_active=True).count(),
        'page_title': 'Medical Lab Booking System - Reliable Diagnostic Services',
    }
    return render(request, 'booking/home.html', context)


def test_catalog(request):
    """Medical test catalog with search and category filtering"""
    tests = Test.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.all()

    category_slug = request.GET.get('category')
    search_query = request.GET.get('q')

    if category_slug:
        tests = tests.filter(category__slug=category_slug)
    if search_query:
        tests = tests.filter(
            Q(test_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(code__icontains=search_query)
        )

    paginator = Paginator(tests.order_by('test_name'), 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_slug,
        'search_query': search_query,
        'page_title': 'Test Catalog & Diagnostic Services',
    }
    return render(request, 'booking/test_catalog.html', context)


def test_detail(request, test_id):
    """Display details of a specific test"""
    test = get_object_or_404(Test, id=test_id, is_active=True)

    recent_bookings = Booking.objects.filter(
        test=test,
        booking_date__gte=date.today(),
        status__in=['pending', 'confirmed']
    ).order_by('booking_date', 'booking_time')[:5]

    context = {
        'test': test,
        'recent_bookings': recent_bookings,
        'page_title': f'{test.test_name} - Diagnostic Test Details',
    }
    return render(request, 'booking/test_detail.html', context)


# ------------------------------------------------------------------
# AUTHENTICATION & PROFILE VIEWS
# ------------------------------------------------------------------

def register_view(request):
    """Register a new patient account"""
    if request.user.is_authenticated:
        return redirect('booking:patient_dashboard')

    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                user = form.save()
                Patient.objects.create(
                    user=user,
                    name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}".strip(),
                    age=form.cleaned_data['age'],
                    gender=form.cleaned_data['gender'],
                    phone=form.cleaned_data['phone'],
                    email=form.cleaned_data['email'],
                    address=form.cleaned_data['address']
                )
                login(request, user)
                messages.success(request, f'Welcome {user.first_name}! Your account has been registered successfully.')
                return redirect('booking:patient_dashboard')
    else:
        form = PatientRegisterForm()

    return render(request, 'booking/register.html', {
        'form': form,
        'page_title': 'Patient Registration',
    })


def login_view(request):
    """Patient & Staff Login"""
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('booking:admin_dashboard')
        return redirect('booking:patient_dashboard')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.is_staff:
                return redirect('booking:admin_dashboard')
            return redirect('booking:patient_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()

    return render(request, 'booking/login.html', {
        'form': form,
        'page_title': 'Account Login',
    })


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('booking:home')


@login_required
def patient_dashboard(request):
    """Authenticated Patient Dashboard"""
    patient = getattr(request.user, 'patient_profile', None)

    if not patient:
        messages.warning(request, 'Please complete your patient profile to access the dashboard.')
        return redirect('booking:patient_profile')

    bookings = Booking.objects.filter(patient=patient).select_related('test', 'test__category')
    upcoming_bookings = [b for b in bookings if b.is_upcoming]
    recent_bookings = bookings.order_by('-created_at')[:5]

    context = {
        'patient': patient,
        'upcoming_bookings': upcoming_bookings,
        'recent_bookings': recent_bookings,
        'total_bookings_count': bookings.count(),
        'page_title': 'Patient Dashboard',
    }
    return render(request, 'booking/dashboard.html', context)


@login_required
def patient_profile(request):
    """Update patient contact and profile information"""
    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={
            'name': request.user.get_full_name() or request.user.username,
            'email': request.user.email or '',
            'age': 25,
            'gender': 'M',
            'phone': '1234567890',
            'address': 'Update address here'
        }
    )

    if request.method == 'POST':
        form = PatientProfileForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile details have been updated.')
            return redirect('booking:patient_dashboard')
    else:
        form = PatientProfileForm(instance=patient)

    return render(request, 'booking/profile.html', {
        'form': form,
        'patient': patient,
        'page_title': 'My Profile & Contact Info',
    })


# ------------------------------------------------------------------
# BOOKING WORKFLOW & ACTIONS
# ------------------------------------------------------------------

def book_test(request, test_id=None):
    """Book a test with optional pre-selected test"""
    selected_test = get_object_or_404(Test, id=test_id, is_active=True) if test_id else None

    # Auto-fill patient details if user is logged in with a profile
    initial_data = {}
    if selected_test:
        initial_data['test'] = selected_test

    if request.user.is_authenticated and hasattr(request.user, 'patient_profile'):
        patient = request.user.patient_profile
        initial_data.update({
            'patient_name': patient.name,
            'patient_age': patient.age,
            'patient_gender': patient.gender,
            'patient_phone': patient.phone,
            'patient_email': patient.email,
            'patient_address': patient.address,
        })

    if request.method == 'POST':
        form = CombinedBookingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    patient_data = {
                        'name': form.cleaned_data['patient_name'],
                        'age': form.cleaned_data['patient_age'],
                        'gender': form.cleaned_data['patient_gender'],
                        'phone': form.cleaned_data['patient_phone'],
                        'email': form.cleaned_data['patient_email'],
                        'address': form.cleaned_data['patient_address'],
                    }

                    if request.user.is_authenticated:
                        patient, created = Patient.objects.get_or_create(user=request.user, defaults=patient_data)
                        if not created:
                            for key, val in patient_data.items():
                                setattr(patient, key, val)
                            patient.save()
                    else:
                        patient, created = Patient.objects.get_or_create(
                            email=patient_data['email'],
                            defaults=patient_data
                        )
                        if not created:
                            for key, val in patient_data.items():
                                setattr(patient, key, val)
                            patient.save()

                    booking = Booking.objects.create(
                        patient=patient,
                        test=form.cleaned_data['test'],
                        booking_date=form.cleaned_data['booking_date'],
                        booking_time=form.cleaned_data['booking_time'],
                        notes=form.cleaned_data.get('notes', ''),
                        status=Booking.STATUS_PENDING
                    )

                    messages.success(
                        request,
                        f'Booking created! Reference number: {booking.reference_number}.'
                    )
                    return redirect('booking:booking_success', reference_number=booking.reference_number)

            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
    else:
        form = CombinedBookingForm(initial=initial_data)

    return render(request, 'booking/booking_form.html', {
        'form': form,
        'selected_test': selected_test,
        'page_title': 'Book Medical Test',
    })


def booking_success(request, reference_number):
    """Display booking confirmation screen"""
    booking = get_object_or_404(Booking.objects.select_related('patient', 'test'), reference_number=reference_number)

    # Authorization check if user is logged in
    if request.user.is_authenticated and not request.user.is_staff:
        if hasattr(request.user, 'patient_profile') and booking.patient != request.user.patient_profile:
            return HttpResponseForbidden("You are not authorized to view this booking.")

    return render(request, 'booking/booking_success.html', {
        'booking': booking,
        'page_title': f'Booking Confirmed - {booking.reference_number}',
    })


def booking_detail(request, reference_number):
    """View details of a specific booking"""
    booking = get_object_or_404(Booking.objects.select_related('patient', 'test', 'test__category'), reference_number=reference_number)

    # Authorization: Patient can only view their own booking
    if request.user.is_authenticated and not request.user.is_staff:
        if hasattr(request.user, 'patient_profile') and booking.patient != request.user.patient_profile:
            return HttpResponseForbidden("Access Denied: You cannot view another patient's booking.")

    return render(request, 'booking/booking_detail.html', {
        'booking': booking,
        'page_title': f'Booking Details - {booking.reference_number}',
    })


def cancel_booking(request, reference_number):
    """Cancel an active booking if permitted"""
    booking = get_object_or_404(Booking, reference_number=reference_number)

    # Authorization
    if request.user.is_authenticated and not request.user.is_staff:
        if hasattr(request.user, 'patient_profile') and booking.patient != request.user.patient_profile:
            return HttpResponseForbidden("Access Denied.")

    if not booking.can_cancel:
        messages.error(request, f'Booking {booking.reference_number} cannot be cancelled at stage: {booking.get_status_display()}.')
        return redirect('booking:booking_detail', reference_number=booking.reference_number)

    if request.method == 'POST':
        booking.status = Booking.STATUS_CANCELLED
        booking.save()
        messages.success(request, f'Booking {booking.reference_number} has been cancelled successfully.')
        if request.user.is_authenticated:
            return redirect('booking:patient_dashboard')
        return redirect('booking:home')

    return render(request, 'booking/cancel_confirm.html', {
        'booking': booking,
        'page_title': f'Cancel Booking {booking.reference_number}',
    })


def my_bookings(request):
    """Lookup patient bookings by email/phone or logged-in user session"""
    bookings = []
    patient = None

    if request.user.is_authenticated and hasattr(request.user, 'patient_profile'):
        patient = request.user.patient_profile
        bookings = Booking.objects.filter(patient=patient).select_related('test').order_by('-created_at')
    elif request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        phone = request.POST.get('phone', '').strip()

        if email or phone:
            try:
                if email and phone:
                    patient = Patient.objects.get(email=email, phone__icontains=phone[-10:])
                elif email:
                    patient = Patient.objects.get(email=email)
                elif phone:
                    patient = Patient.objects.get(phone__icontains=phone[-10:])

                if patient:
                    bookings = Booking.objects.filter(patient=patient).select_related('test').order_by('-created_at')
                    messages.success(request, f'Found {bookings.count()} booking(s) for {patient.name}')

            except Patient.DoesNotExist:
                messages.error(request, 'No patient record found matching those details.')
            except Patient.MultipleObjectsReturned:
                messages.error(request, 'Multiple patient records found. Please contact lab support.')
        else:
            messages.error(request, 'Please provide email or phone number.')

    return render(request, 'booking/my_bookings.html', {
        'bookings': bookings,
        'patient': patient,
        'page_title': 'My Bookings & History',
    })


# ------------------------------------------------------------------
# ADMIN & STAFF MANAGEMENT DASHBOARD
# ------------------------------------------------------------------

@user_passes_test(lambda u: u.is_staff)
def admin_dashboard(request):
    """Staff Lab Management Dashboard with key metrics and filters"""
    today = date.today()

    all_bookings = Booking.objects.select_related('patient', 'test')

    # Filter controls
    status_filter = request.GET.get('status')
    date_filter = request.GET.get('date')
    search_query = request.GET.get('search')

    filtered_bookings = all_bookings
    if status_filter:
        filtered_bookings = filtered_bookings.filter(status=status_filter)
    if date_filter:
        filtered_bookings = filtered_bookings.filter(booking_date=date_filter)
    if search_query:
        filtered_bookings = filtered_bookings.filter(
            Q(reference_number__icontains=search_query) |
            Q(patient__name__icontains=search_query) |
            Q(patient__phone__icontains=search_query) |
            Q(test__test_name__icontains=search_query)
        )

    # Metrics
    stats = {
        'total_patients': Patient.objects.count(),
        'total_bookings': all_bookings.count(),
        'today_bookings': all_bookings.filter(booking_date=today).count(),
        'pending_bookings': all_bookings.filter(status=Booking.STATUS_PENDING).count(),
        'confirmed_bookings': all_bookings.filter(status=Booking.STATUS_CONFIRMED).count(),
        'completed_bookings': all_bookings.filter(status=Booking.STATUS_COMPLETED).count(),
        'cancelled_bookings': all_bookings.filter(status=Booking.STATUS_CANCELLED).count(),
        'total_revenue': all_bookings.filter(
            status__in=[Booking.STATUS_CONFIRMED, Booking.STATUS_SAMPLE_COLLECTED, Booking.STATUS_PROCESSING, Booking.STATUS_COMPLETED]
        ).aggregate(total=Sum('test__price'))['total'] or 0,
    }

    popular_tests = Test.objects.annotate(
        booking_count=Count('bookings')
    ).order_by('-booking_count')[:5]

    paginator = Paginator(filtered_bookings.order_by('-created_at'), 15)
    page_number = request.GET.get('page')
    bookings_page = paginator.get_page(page_number)

    return render(request, 'booking/admin_dashboard.html', {
        'stats': stats,
        'popular_tests': popular_tests,
        'bookings_page': bookings_page,
        'status_choices': Booking.STATUS_CHOICES,
        'selected_status': status_filter,
        'selected_date': date_filter,
        'search_query': search_query,
        'page_title': 'Staff Administrative Dashboard',
    })


@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def update_booking_status(request, booking_id):
    """Admin endpoint to update booking status along the workflow"""
    booking = get_object_or_404(Booking, id=booking_id)
    new_status = request.POST.get('status')

    if new_status in dict(Booking.STATUS_CHOICES):
        try:
            booking.status = new_status
            booking.save()
            messages.success(request, f'Status for booking {booking.reference_number} updated to {booking.get_status_display()}.')
        except Exception as e:
            messages.error(request, f'Failed to update status: {str(e)}')
    else:
        messages.error(request, 'Invalid status choice.')

    return redirect('booking:admin_dashboard')


# ------------------------------------------------------------------
# AJAX & API ENDPOINTS
# ------------------------------------------------------------------

@require_http_methods(["GET"])
def check_availability(request):
    """AJAX view to check slot availability"""
    test_id = request.GET.get('test_id')
    booking_date = request.GET.get('booking_date')

    if not test_id or not booking_date:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        test = Test.objects.get(id=test_id, is_active=True)
        existing_bookings = Booking.objects.filter(
            test=test,
            booking_date=booking_date,
            status__in=[Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED, Booking.STATUS_SAMPLE_COLLECTED, Booking.STATUS_PROCESSING]
        ).values_list('booking_time', flat=True)

        booked_times = [t.strftime('%H:%M') for t in existing_bookings]

        return JsonResponse({
            'booked_times': booked_times,
            'test_name': test.test_name,
            'duration': test.duration_hours
        })
    except Test.DoesNotExist:
        return JsonResponse({'error': 'Test not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_tests(request):
    """API endpoint to retrieve test listing"""
    tests = Test.objects.filter(is_active=True).values(
        'id', 'test_name', 'description', 'price', 'turnaround_time', 'duration_hours'
    )
    return JsonResponse({'tests': list(tests)})


# ------------------------------------------------------------------
# STATIC CONTENT & ERRORS
# ------------------------------------------------------------------

def about(request):
    return render(request, 'booking/about.html', {'page_title': 'About Our Laboratory'})

def contact(request):
    return render(request, 'booking/contact.html', {'page_title': 'Contact Us'})

def privacy_policy(request):
    return render(request, 'booking/privacy_policy.html', {'page_title': 'Privacy Policy'})

def terms_of_service(request):
    return render(request, 'booking/terms_of_service.html', {'page_title': 'Terms of Service'})

def custom_404(request, exception):
    return render(request, 'booking/404.html', status=404)

def custom_500(request):
    return render(request, 'booking/500.html', status=500)
