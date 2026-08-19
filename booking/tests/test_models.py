from datetime import date, timedelta, time
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from booking.models import Category, Test, Patient, Booking


class ModelTestCase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Hematology",
            slug="hematology",
            description="Blood tests"
        )
        self.test_obj = Test.objects.create(
            category=self.category,
            test_name="Complete Blood Count",
            code="CBC-01",
            description="Measures red/white cells",
            price=500.00,
            turnaround_time="12 Hours"
        )
        self.user = User.objects.create_user(
            username="patient_user",
            email="patient@example.com",
            password="Password123!"
        )
        self.patient = Patient.objects.create(
            user=self.user,
            name="John Doe",
            age=30,
            gender="M",
            phone="+12345678901",
            email="patient@example.com",
            address="123 Main St"
        )

    def test_category_creation(self):
        self.assertEqual(str(self.category), "Hematology")

    def test_patient_creation(self):
        self.assertEqual(str(self.patient), "John Doe (30yrs, Male)")
        self.assertEqual(self.patient.user, self.user)

    def test_test_creation(self):
        self.assertEqual(str(self.test_obj), f"Complete Blood Count (₹{self.test_obj.price})")

    def test_booking_reference_number_and_properties(self):
        tomorrow = date.today() + timedelta(days=1)
        booking = Booking.objects.create(
            patient=self.patient,
            test=self.test_obj,
            booking_date=tomorrow,
            booking_time=time(10, 0),
            status=Booking.STATUS_PENDING
        )
        self.assertTrue(booking.reference_number.startswith("LAB-"))
        self.assertTrue(booking.is_upcoming)
        self.assertTrue(booking.can_cancel)
        self.assertEqual(booking.total_cost, 500.00)

    def test_invalid_past_date_booking(self):
        yesterday = date.today() - timedelta(days=1)
        booking = Booking(
            patient=self.patient,
            test=self.test_obj,
            booking_date=yesterday,
            booking_time=time(10, 0),
            status=Booking.STATUS_PENDING
        )
        with self.assertRaises(ValidationError):
            booking.full_clean()

    def test_status_transition_validation(self):
        tomorrow = date.today() + timedelta(days=1)
        booking = Booking.objects.create(
            patient=self.patient,
            test=self.test_obj,
            booking_date=tomorrow,
            booking_time=time(10, 0),
            status=Booking.STATUS_PENDING
        )
        # Attempt invalid transition from pending directly to completed
        booking.status = Booking.STATUS_COMPLETED
        with self.assertRaises(ValidationError):
            booking.full_clean()

        # Valid transition from pending to confirmed
        booking.status = Booking.STATUS_CONFIRMED
        booking.full_clean()
        booking.save()
        self.assertEqual(booking.status, Booking.STATUS_CONFIRMED)
