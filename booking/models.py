"""
Models for the Medical Lab Booking System
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import date, time


class Patient(models.Model):
    """Model representing a patient"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    name = models.CharField(max_length=100, help_text='Full name of the patient')
    age = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text='Age of the patient'
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone = models.CharField(
        max_length=15, 
        help_text='Contact phone number (include country code if international)'
    )
    email = models.EmailField(help_text='Email address for contact and notifications')
    address = models.TextField(help_text='Full address of the patient')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'

    def __str__(self):
        return f"{self.name} ({self.age}yrs, {self.get_gender_display()})"

    def get_recent_bookings(self):
        """Get recent bookings for this patient"""
        return self.booking_set.all().order_by('-created_at')[:5]


class Test(models.Model):
    """Model representing a medical test"""
    test_name = models.CharField(
        max_length=100, 
        unique=True,
        help_text='Name of the medical test'
    )
    description = models.TextField(help_text='Detailed description of the test')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Price of the test in rupees'
    )
    duration_hours = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(24)],
        help_text='Expected duration of the test in hours'
    )
    is_active = models.BooleanField(
        default=True, 
        help_text='Whether this test is currently available for booking'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['test_name']
        verbose_name = 'Medical Test'
        verbose_name_plural = 'Medical Tests'

    def __str__(self):
        return f"{self.test_name} (₹{self.price})"

    def get_recent_bookings_count(self):
        """Get count of recent bookings for this test"""
        return self.booking_set.filter(created_at__gte=timezone.now().replace(day=1)).count()


class Booking(models.Model):
    """Model representing a booking for a medical test"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE,
        help_text='Patient who made the booking'
    )
    test = models.ForeignKey(
        Test, 
        on_delete=models.CASCADE,
        help_text='Medical test to be performed'
    )
    booking_date = models.DateField(help_text='Date when the test will be performed')
    booking_time = models.TimeField(help_text='Time when the test will be performed')
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
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
        unique_together = ['test', 'booking_date', 'booking_time']

    def __str__(self):
        return f"{self.patient.name} - {self.test.test_name} on {self.booking_date} at {self.booking_time}"

    def clean(self):
        """Validate booking data"""
        from django.core.exceptions import ValidationError

        # Don't allow booking in the past
        if self.booking_date < date.today():
            raise ValidationError('Cannot book for a past date.')

        # Don't allow booking for today if time has passed
        if (self.booking_date == date.today() and 
            self.booking_time <= timezone.now().time()):
            raise ValidationError('Cannot book for a past time today.')

    def save(self, *args, **kwargs):
        """Override save to perform validation"""
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_upcoming(self):
        """Check if the booking is upcoming"""
        today = date.today()
        now = timezone.now().time()

        if self.booking_date > today:
            return True
        elif self.booking_date == today and self.booking_time > now:
            return True
        return False

    @property
    def total_cost(self):
        """Get total cost of the booking"""
        return self.test.price

    def get_status_color(self):
        """Get color code for status display"""
        colors = {
            'pending': '#ffc107',  # yellow
            'confirmed': '#28a745',  # green
            'completed': '#007bff',  # blue
            'cancelled': '#dc3545',  # red
        }
        return colors.get(self.status, '#6c757d')
