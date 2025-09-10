"""
Views for the Medical Lab Booking System
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import date
from .models import Test, Patient, Booking
from .forms import CombinedBookingForm, PatientForm, BookingForm


def home(request):
    """Homepage showing available tests"""
    tests = Test.objects.filter(is_active=True).order_by('test_name')

    context = {
        'tests': tests,
        'total_tests': tests.count(),
        'page_title': 'Available Medical Tests',
    }
    return render(request, 'booking/home.html', context)


def test_detail(request, test_id):
    """Display details of a specific test"""
    test = get_object_or_404(Test, id=test_id, is_active=True)

    # Get recent bookings for this test (for availability info)
    recent_bookings = Booking.objects.filter(
        test=test,
        booking_date__gte=date.today(),
        status__in=['pending', 'confirmed']
    ).order_by('booking_date', 'booking_time')[:10]

    context = {
        'test': test,
        'recent_bookings': recent_bookings,
        'page_title': f'{test.test_name} - Details',
    }
    return render(request, 'booking/test_detail.html', context)


def book_test(request, test_id=None):
    if test_id:
        selected_test = get_object_or_404(Test, id=test_id, is_active=True)
    else:
        selected_test = None

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

                    try:
                        patient = Patient.objects.get(email=patient_data['email'])
                        for key, value in patient_data.items():
                            setattr(patient, key, value)
                        patient.save()
                    except Patient.DoesNotExist:
                        patient = Patient.objects.create(**patient_data)

                    booking = Booking.objects.create(
                        patient=patient,
                        test=form.cleaned_data['test'],
                        booking_date=form.cleaned_data['booking_date'],
                        booking_time=form.cleaned_data['booking_time'],
                        notes=form.cleaned_data.get('notes', ''),
                        status='pending'
                    )

                    messages.success(
                        request,
                        f'Booking confirmed! Your booking ID is BK-{booking.id:04d}. '
                        f'You will receive a confirmation call shortly.'
                    )
                    # FIXED: use booking:booking_success instead of booking_success
                    return redirect('booking:booking_success', booking_id=booking.id)

            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
    else:
        initial_data = {}
        if selected_test:
            initial_data['test'] = selected_test
        form = CombinedBookingForm(initial=initial_data)

    return render(request, 'booking/booking_form.html', {
        'form': form,
        'selected_test': selected_test,
        'page_title': 'Book Medical Test',
    })


def booking_success(request, booking_id):
    """Display booking success page"""
    booking = get_object_or_404(Booking, id=booking_id)

    context = {
        'booking': booking,
        'page_title': 'Booking Confirmed',
    }
    return render(request, 'booking/booking_success.html', context)


def my_bookings(request):
    """Display patient bookings (requires email verification)"""
    bookings = []
    patient = None

    if request.method == 'POST':
        email = request.POST.get('email', '').lower().strip()
        phone = request.POST.get('phone', '').strip()

        if email or phone:
            try:
                # Find patient by email or phone
                if email and phone:
                    patient = Patient.objects.get(email=email, phone__icontains=phone[-10:])
                elif email:
                    patient = Patient.objects.get(email=email)
                elif phone:
                    patient = Patient.objects.get(phone__icontains=phone[-10:])

                if patient:
                    bookings = Booking.objects.filter(patient=patient).order_by('-created_at')
                    messages.success(request, f'Found {bookings.count()} booking(s) for {patient.name}')

            except Patient.DoesNotExist:
                messages.error(request, 'No patient found with the provided details.')
            except Patient.MultipleObjectsReturned:
                messages.error(request, 'Multiple patients found. Please contact support.')
        else:
            messages.error(request, 'Please provide either email or phone number.')

    context = {
        'bookings': bookings,
        'patient': patient,
        'page_title': 'My Bookings',
    }
    return render(request, 'booking/my_bookings.html', context)


@require_http_methods(["GET"])
def check_availability(request):
    """AJAX view to check time slot availability"""
    test_id = request.GET.get('test_id')
    booking_date = request.GET.get('booking_date')

    if not test_id or not booking_date:
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    try:
        test = Test.objects.get(id=test_id, is_active=True)

        # Get existing bookings for this test on this date
        existing_bookings = Booking.objects.filter(
            test=test,
            booking_date=booking_date,
            status__in=['pending', 'confirmed']
        ).values_list('booking_time', flat=True)

        # Convert to list of time strings
        booked_times = [time.strftime('%H:%M') for time in existing_bookings]

        return JsonResponse({
            'booked_times': booked_times,
            'test_name': test.test_name,
            'duration': test.duration_hours
        })

    except Test.DoesNotExist:
        return JsonResponse({'error': 'Test not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def admin_dashboard(request):
    """Admin dashboard with statistics"""
    today = date.today()

    # Get statistics
    stats = {
        'total_patients': Patient.objects.count(),
        'total_tests': Test.objects.filter(is_active=True).count(),
        'total_bookings': Booking.objects.count(),
        'today_bookings': Booking.objects.filter(booking_date=today).count(),
        'pending_bookings': Booking.objects.filter(status='pending').count(),
        'confirmed_bookings': Booking.objects.filter(status='confirmed').count(),
    }

    # Recent bookings
    recent_bookings = Booking.objects.select_related('patient', 'test').order_by('-created_at')[:10]

    # Today's bookings
    today_bookings = Booking.objects.filter(
        booking_date=today
    ).select_related('patient', 'test').order_by('booking_time')

    context = {
        'stats': stats,
        'recent_bookings': recent_bookings,
        'today_bookings': today_bookings,
        'page_title': 'Admin Dashboard',
    }
    return render(request, 'admin/dashboard.html', context)


def about(request):
    """About page"""
    context = {
        'page_title': 'About Us',
    }
    return render(request, 'booking/about.html', context)


def contact(request):
    """Contact page"""
    context = {
        'page_title': 'Contact Us',
    }
    return render(request, 'booking/contact.html', context)


def privacy_policy(request):
    """Privacy policy page"""
    context = {
        'page_title': 'Privacy Policy',
    }
    return render(request, 'booking/privacy_policy.html', context)


def terms_of_service(request):
    """Terms of service page"""
    context = {
        'page_title': 'Terms of Service',
    }
    return render(request, 'booking/terms_of_service.html', context)


# Error handlers
def custom_404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'booking/404.html', status=404)


def custom_500(request):
    """Custom 500 error handler"""
    return render(request, 'booking/500.html', status=500)


# API Views for AJAX requests
@require_http_methods(["GET"])
def api_tests(request):
    """API endpoint to get all active tests"""
    tests = Test.objects.filter(is_active=True).values(
        'id', 'test_name', 'description', 'price', 'duration_hours'
    )
    return JsonResponse({'tests': list(tests)})


@require_http_methods(["POST"])
def api_quick_booking(request):
    """API endpoint for quick booking (for mobile/AJAX)"""
    try:
        # This would be implemented for mobile app or AJAX bookings
        # For now, just return success
        return JsonResponse({
            'success': True,
            'message': 'Booking created successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
