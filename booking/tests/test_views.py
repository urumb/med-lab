from datetime import date, timedelta, time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from booking.models import Category, Test, Patient, Booking


class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Biochemistry", slug="biochemistry")
        self.test_obj = Test.objects.create(
            category=self.category,
            test_name="Lipid Profile",
            price=750.00,
            is_active=True
        )

        # Patient User
        self.patient_user = User.objects.create_user(
            username="testpatient",
            email="patient@test.com",
            password="Password123!"
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            name="Test Patient",
            age=28,
            gender="F",
            phone="+1234567890",
            email="patient@test.com",
            address="456 Health St"
        )

        # Staff User
        self.staff_user = User.objects.create_user(
            username="staffuser",
            email="staff@test.com",
            password="Password123!",
            is_staff=True
        )

        # Booking
        self.booking = Booking.objects.create(
            patient=self.patient,
            test=self.test_obj,
            booking_date=date.today() + timedelta(days=2),
            booking_time=time(10, 0),
            status=Booking.STATUS_PENDING
        )

    def test_homepage_view(self):
        response = self.client.get(reverse('booking:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "MedLab")

    def test_test_catalog_view(self):
        response = self.client.get(reverse('booking:test_catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lipid Profile")

    def test_test_detail_view(self):
        response = self.client.get(reverse('booking:test_detail', args=[self.test_obj.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Lipid Profile")

    def test_booking_creation_submission(self):
        tomorrow = date.today() + timedelta(days=3)
        post_data = {
            'patient_name': 'New Patient',
            'patient_age': 35,
            'patient_gender': 'M',
            'patient_phone': '+1987654321',
            'patient_email': 'newpatient@test.com',
            'patient_address': '789 Oak St',
            'test': self.test_obj.id,
            'booking_date': tomorrow.strftime('%Y-%m-%d'),
            'booking_time': '11:00',
            'notes': 'Fasting completed'
        }
        response = self.client.post(reverse('booking:book_test'), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Booking.objects.filter(patient__email='newpatient@test.com').exists())

    def test_patient_dashboard_access_control(self):
        # Unauthenticated access redirects to login
        response = self.client.get(reverse('booking:patient_dashboard'))
        self.assertEqual(response.status_code, 302)

        # Authenticated patient access
        self.client.login(username='testpatient', password='Password123!')
        response = self.client.get(reverse('booking:patient_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Patient")

    def test_patient_cannot_view_other_patient_booking(self):
        other_user = User.objects.create_user(username="otherpatient", password="Password123!")
        other_patient = Patient.objects.create(
            user=other_user, name="Other", age=40, gender="M", phone="+1111111111", email="other@test.com", address="XYZ"
        )
        self.client.login(username='otherpatient', password='Password123!')

        response = self.client.get(reverse('booking:booking_detail', args=[self.booking.reference_number]))
        self.assertEqual(response.status_code, 403)

    def test_staff_dashboard_access(self):
        # Regular patient forbidden
        self.client.login(username='testpatient', password='Password123!')
        response = self.client.get(reverse('booking:admin_dashboard'))
        self.assertEqual(response.status_code, 302)

        # Staff user allowed
        self.client.login(username='staffuser', password='Password123!')
        response = self.client.get(reverse('booking:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Laboratory Management Dashboard")

    def test_booking_cancellation(self):
        self.client.login(username='testpatient', password='Password123!')
        response = self.client.post(reverse('booking:cancel_booking', args=[self.booking.reference_number]))
        self.assertEqual(response.status_code, 302)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.STATUS_CANCELLED)
