"""
Forms for the Medical Lab Booking System
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, datetime
from .models import Patient, Booking, Test


class PatientForm(forms.ModelForm):
    """Form for patient information"""

    class Meta:
        model = Patient
        fields = ['name', 'age', 'gender', 'phone', 'email', 'address']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter full name',
                'required': True
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 120,
                'placeholder': 'Enter age',
                'required': True
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XXXXXXXXXX',
                'title': 'Enter a valid phone number',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@example.com',
                'required': True
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter complete address',
                'required': True
            }),
        }
        labels = {
            'name': 'Full Name',
            'age': 'Age (years)',
            'gender': 'Gender',
            'phone': 'Phone Number',
            'email': 'Email Address',
            'address': 'Address',
        }

    def clean_name(self):
        """Validate and clean name field"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip().title()
            if len(name) < 2:
                raise ValidationError('Name must be at least 2 characters long.')
            if not all(c.isalpha() or c.isspace() for c in name):
                raise ValidationError('Name should contain only letters and spaces.')
        return name

    def clean_phone(self):
        """Validate and clean phone field"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove all non-digit characters except +
            cleaned_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
            if len(cleaned_phone) < 10:
                raise ValidationError('Phone number must be at least 10 digits.')
            return cleaned_phone
        return phone

    def clean_email(self):
        """Validate and clean email field"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email


class BookingForm(forms.ModelForm):
    """Form for booking a medical test"""

    class Meta:
        model = Booking
        fields = ['test', 'booking_date', 'booking_time', 'notes']
        widgets = {
            'test': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'booking_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
            'booking_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Any special instructions or notes (optional)'
            }),
        }
        labels = {
            'test': 'Select Medical Test',
            'booking_date': 'Preferred Date',
            'booking_time': 'Preferred Time',
            'notes': 'Additional Notes',
        }

    def __init__(self, *args, **kwargs):
        """Initialize form with active tests only"""
        super().__init__(*args, **kwargs)

        # Only show active tests
        self.fields['test'].queryset = Test.objects.filter(is_active=True).order_by('test_name')

        # Set minimum date to today
        today = date.today().isoformat()
        self.fields['booking_date'].widget.attrs['min'] = today

        # Add help text
        self.fields['booking_date'].help_text = 'Select a date from today onwards'
        self.fields['booking_time'].help_text = 'Lab hours: 8:00 AM to 8:00 PM'

    def clean_booking_date(self):
        """Validate booking date"""
        booking_date = self.cleaned_data.get('booking_date')
        if booking_date:
            if booking_date < date.today():
                raise ValidationError('Cannot book for a past date.')
        return booking_date

    def clean_booking_time(self):
        """Validate booking time"""
        booking_time = self.cleaned_data.get('booking_time')
        if booking_time:
            # Lab hours: 8:00 AM to 8:00 PM
            lab_open = datetime.strptime('08:00', '%H:%M').time()
            lab_close = datetime.strptime('20:00', '%H:%M').time()

            if booking_time < lab_open or booking_time > lab_close:
                raise ValidationError('Lab hours are from 8:00 AM to 8:00 PM.')

            # Check if booking is for today and time has passed
            booking_date = self.cleaned_data.get('booking_date')
            if booking_date == date.today():
                current_time = timezone.now().time()
                if booking_time <= current_time:
                    raise ValidationError('Cannot book for a past time today.')

        return booking_time

    def clean(self):
        """Validate the complete form"""
        cleaned_data = super().clean()
        test = cleaned_data.get('test')
        booking_date = cleaned_data.get('booking_date')
        booking_time = cleaned_data.get('booking_time')

        if test and booking_date and booking_time:
            # Check for conflicting bookings
            existing_booking = Booking.objects.filter(
                test=test,
                booking_date=booking_date,
                booking_time=booking_time,
                status__in=['pending', 'confirmed']
            ).exists()

            if existing_booking:
                raise ValidationError(
                    f'This time slot is already booked for {test.test_name}. '
                    'Please select a different time.'
                )

        return cleaned_data


class CombinedBookingForm(forms.Form):
    """Combined form for patient info and booking"""

    # Patient fields
    patient_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter full name',
            'required': True
        }),
        label='Full Name'
    )

    patient_age = forms.IntegerField(
        min_value=1,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter age',
            'required': True
        }),
        label='Age (years)'
    )

    patient_gender = forms.ChoiceField(
        choices=Patient.GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        label='Gender'
    )

    patient_phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXXXXXXXXX',
            'required': True
        }),
        label='Phone Number'
    )

    patient_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com',
            'required': True
        }),
        label='Email Address'
    )

    patient_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter complete address',
            'required': True
        }),
        label='Address'
    )

    # Booking fields
    test = forms.ModelChoiceField(
        queryset=Test.objects.filter(is_active=True).order_by('test_name'),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'required': True
        }),
        label='Select Medical Test'
    )

    booking_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'required': True
        }),
        label='Preferred Date'
    )

    booking_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time',
            'required': True
        }),
        label='Preferred Time'
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special instructions or notes (optional)'
        }),
        label='Additional Notes'
    )

    def __init__(self, *args, **kwargs):
        """Initialize combined form"""
        super().__init__(*args, **kwargs)

        # Set minimum date to today
        today = date.today().isoformat()
        self.fields['booking_date'].widget.attrs['min'] = today

        # Add help text
        self.fields['booking_date'].help_text = 'Select a date from today onwards'
        self.fields['booking_time'].help_text = 'Lab hours: 8:00 AM to 8:00 PM'

    def clean(self):
        """Validate the combined form"""
        cleaned_data = super().clean()

        # Validate patient data
        name = cleaned_data.get('patient_name')
        if name:
            name = name.strip().title()
            if len(name) < 2:
                self.add_error('patient_name', 'Name must be at least 2 characters long.')

        # Validate booking data
        booking_date = cleaned_data.get('booking_date')
        booking_time = cleaned_data.get('booking_time')
        test = cleaned_data.get('test')

        if booking_date and booking_date < date.today():
            self.add_error('booking_date', 'Cannot book for a past date.')

        if booking_time:
            lab_open = datetime.strptime('08:00', '%H:%M').time()
            lab_close = datetime.strptime('20:00', '%H:%M').time()

            if booking_time < lab_open or booking_time > lab_close:
                self.add_error('booking_time', 'Lab hours are from 8:00 AM to 8:00 PM.')

        # Check for conflicts
        if test and booking_date and booking_time:
            existing_booking = Booking.objects.filter(
                test=test,
                booking_date=booking_date,
                booking_time=booking_time,
                status__in=['pending', 'confirmed']
            ).exists()

            if existing_booking:
                self.add_error('booking_time',
                    f'This time slot is already booked for {test.test_name}. '
                    'Please select a different time.'
                )

        return cleaned_data
