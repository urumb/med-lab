"""
Models for the Medical Lab Booking System
"""
import uuid
from datetime import date, datetime
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


def generate_reference_number():
    """Generates a unique reference number formatted like LAB-YYYYMMDD-XXXX"""
    date_str = date.today().strftime('%Y%m%d')
    unique_suffix = uuid.uuid4().hex[:4].upper()
    return f"LAB-{date_str}-{unique_suffix}"


class Category(models.Model):
    """Category for grouping medical tests (e.g. Hematology, Biochemistry, Radiology, Pathology)"""
    name = models.CharField(max_length=100, unique=True, help_text='Name of the test category')
    slug = models.SlugField(max_length=100, unique=True, help_text='URL-friendly identifier')
    description = models.TextField(blank=True, help_text='Category description and scope')
    icon = models.CharField(
        max_length=50,
        default='bi-journal-medical',
        help_text='Bootstrap icon class name (e.g., bi-droplet-half)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Test Category'
        verbose_name_plural = 'Test Categories'

    def __str__(self):
        return self.name


class Patient(models.Model):
    """Model representing a patient profile, optionally linked to a Django User account"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='patient_profile',
        help_text='Associated user account if registered'
    )
    name = models.CharField(max_length=100, help_text='Full name of the patient')
    age = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text='Age of the patient'
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number (e.g. +1234567890 or 9876543210)')],
        help_text='Contact phone number'
    )
    email = models.EmailField(help_text='Email address for notifications and account verification')
    address = models.TextField(help_text='Full address of the patient')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f"{self.name} ({self.age}yrs, {self.get_gender_display()})"

    def get_recent_bookings(self):
        """Get recent bookings for this patient"""
        return self.bookings.select_related('test', 'test__category').order_by('-created_at')[:5]


class Test(models.Model):
    """Model representing a medical laboratory test"""
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tests',
        help_text='Category of the test'
    )
    test_name = models.CharField(
        max_length=100,
        unique=True,
        help_text='Name of the medical test'
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text='Unique test code (e.g. CBC-01)'
    )
    description = models.TextField(help_text='Detailed description of the test and what it diagnoses')
    preparation_instructions = models.TextField(
        blank=True,
        default='No special fasting required unless instructed by your physician.',
        help_text='Patient preparation guidelines (e.g. Fasting 8-10 hours)'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Price of the test'
    )
    turnaround_time = models.CharField(
        max_length=50,
        default='24 Hours',
        help_text='Estimated time to deliver results (e.g. 12 Hours, 2 Days)'
    )
    duration_hours = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        help_text='Expected duration of the sample collection procedure in hours'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this test is currently available for booking'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['test_name']
        verbose_name = 'Medical Test'
        verbose_name_plural = 'Medical Tests'
        indexes = [
            models.Index(fields=['is_active', 'test_name']),
        ]

    def __str__(self):
        return f"{self.test_name} (₹{self.price})"

    def get_recent_bookings_count(self):
        """Get count of recent bookings for this test"""
        first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.bookings.filter(created_at__gte=first_day_of_month).count()


class Booking(models.Model):
    """Model representing a booking for a medical test"""

    # Status Workflow Constants
    STATUS_PENDING = 'pending'
    STATUS_CONFIRMED = 'confirmed'
    STATUS_SAMPLE_COLLECTED = 'sample_collected'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_SAMPLE_COLLECTED, 'Sample Collected'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    ALLOWED_TRANSITIONS = {
        STATUS_PENDING: [STATUS_CONFIRMED, STATUS_CANCELLED],
        STATUS_CONFIRMED: [STATUS_SAMPLE_COLLECTED, STATUS_CANCELLED],
        STATUS_SAMPLE_COLLECTED: [STATUS_PROCESSING, STATUS_CANCELLED],
        STATUS_PROCESSING: [STATUS_COMPLETED, STATUS_CANCELLED],
        STATUS_COMPLETED: [],
        STATUS_CANCELLED: [],
    }

    reference_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        editable=False,
        help_text='Unique booking reference code (e.g. LAB-20250101-ABCD)'
    )
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='bookings',
        help_text='Patient who made the booking'
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='bookings',
        help_text='Medical test to be performed'
    )
    booking_date = models.DateField(help_text='Date when the test will be performed')
    booking_time = models.TimeField(help_text='Time when the test will be performed')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        help_text='Current status of the booking'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes or special instructions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-booking_date', '-booking_time']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
        constraints = [
            models.UniqueConstraint(
                fields=['test', 'booking_date', 'booking_time'],
                condition=models.Q(status__in=['pending', 'confirmed', 'sample_collected', 'processing']),
                name='unique_active_booking_slot'
            )
        ]
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['booking_date', 'booking_time']),
            models.Index(fields=['reference_number']),
        ]

    def __str__(self):
        return f"{self.reference_number} - {self.patient.name} - {self.test.test_name} ({self.get_status_display()})"

    def clean(self):
        """Validate booking date, time and status transitions"""
        # Validate date
        if self._state.adding and self.booking_date < date.today():
            raise ValidationError({'booking_date': 'Cannot book for a past date.'})

        # Validate time today
        if self._state.adding and self.booking_date == date.today() and self.booking_time <= timezone.now().time():
            raise ValidationError({'booking_time': 'Cannot book for a past time today.'})

        # Validate Status transition if updated
        if self.pk:
            original = Booking.objects.get(pk=self.pk)
            if original.status != self.status:
                allowed = self.ALLOWED_TRANSITIONS.get(original.status, [])
                if self.status not in allowed:
                    raise ValidationError(
                        f'Invalid status transition from {original.get_status_display()} to {self.get_status_display()}.'
                    )

    def save(self, *args, **kwargs):
        """Override save to perform validation and assign reference number"""
        if not self.reference_number:
            self.reference_number = generate_reference_number()
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        """Check if the booking is upcoming"""
        if self.status in [self.STATUS_CANCELLED, self.STATUS_COMPLETED]:
            return False
        today = date.today()
        now = timezone.now().time()
        if self.booking_date > today:
            return True
        elif self.booking_date == today and self.booking_time > now:
            return True
        return False

    @property
    def can_cancel(self):
        """Check if patient can cancel this booking"""
        return self.status in [self.STATUS_PENDING, self.STATUS_CONFIRMED]

    @property
    def total_cost(self):
        """Get total cost of the booking"""
        return self.test.price

    def get_status_badge_class(self):
        """Get Bootstrap badge class for status"""
        badge_classes = {
            self.STATUS_PENDING: 'bg-warning text-dark',
            self.STATUS_CONFIRMED: 'bg-info text-white',
            self.STATUS_SAMPLE_COLLECTED: 'bg-primary text-white',
            self.STATUS_PROCESSING: 'bg-purple text-white',
            self.STATUS_COMPLETED: 'bg-success text-white',
            self.STATUS_CANCELLED: 'bg-danger text-white',
        }
        return badge_classes.get(self.status, 'bg-secondary text-white')

    def get_status_color(self):
        """Get color code for status display"""
        colors = {
            self.STATUS_PENDING: '#ffc107',
            self.STATUS_CONFIRMED: '#17a2b8',
            self.STATUS_SAMPLE_COLLECTED: '#0d6efd',
            self.STATUS_PROCESSING: '#6f42c1',
            self.STATUS_COMPLETED: '#198754',
            self.STATUS_CANCELLED: '#dc3545',
        }
        return colors.get(self.status, '#6c757d')
