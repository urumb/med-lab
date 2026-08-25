from datetime import date, timedelta, time
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from booking.models import Category, Test, Patient, Booking


class SecurityAndAccessTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Radiology", slug="radiology")
        self.test_obj = Test.objects.create(category=self.category, test_name="X-Ray Chest", price=600.00)

        self.patient_user1 = User.objects.create_user(username="patient1", password="Password123!")
        self.patient1 = Patient.objects.create(user=self.patient_user1, name="Patient One", age=30, gender="M", phone="+1111111111", email="p1@test.com", address="Addr 1")

        self.patient_user2 = User.objects.create_user(username="patient2", password="Password123!")
        self.patient2 = Patient.objects.create(user=self.patient_user2, name="Patient Two", age=25, gender="F", phone="+2222222222", email="p2@test.com", address="Addr 2")

        self.booking1 = Booking.objects.create(patient=self.patient1, test=self.test_obj, booking_date=date.today()+timedelta(days=1), booking_time=time(9,0))

    def test_unauthenticated_dashboard_redirect(self):
        response = self.client.get(reverse('booking:patient_dashboard'))
        self.assertRedirects(response, f"{reverse('booking:login')}?next={reverse('booking:patient_dashboard')}")

    def test_cross_patient_booking_access_forbidden(self):
        self.client.login(username="patient2", password="Password123!")
        response = self.client.get(reverse('booking:booking_detail', args=[self.booking1.reference_number]))
        self.assertEqual(response.status_code, 403)

    def test_cross_patient_receipt_access_forbidden(self):
        self.client.login(username="patient2", password="Password123!")
        response = self.client.get(reverse('booking:booking_receipt', args=[self.booking1.reference_number]))
        self.assertEqual(response.status_code, 403)

    def test_patient_access_own_receipt(self):
        self.client.login(username="patient1", password="Password123!")
        response = self.client.get(reverse('booking:booking_receipt', args=[self.booking1.reference_number]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "OFFICIAL RECEIPT")


class CatalogSearchSortTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.cat1 = Category.objects.create(name="Blood", slug="blood")
        self.cat2 = Category.objects.create(name="Urine", slug="urine")
        self.t1 = Test.objects.create(category=self.cat1, test_name="Blood Sugar", code="BS-01", price=200.00)
        self.t2 = Test.objects.create(category=self.cat2, test_name="Urine Culture", code="UC-02", price=800.00)

    def test_catalog_category_filter(self):
        response = self.client.get(f"{reverse('booking:test_catalog')}?category=blood")
        self.assertContains(response, "Blood Sugar")
        self.assertNotContains(response, "Urine Culture")

    def test_catalog_search_query(self):
        response = self.client.get(f"{reverse('booking:test_catalog')}?q=Culture")
        self.assertContains(response, "Urine Culture")
        self.assertNotContains(response, "Blood Sugar")

    def test_catalog_price_sorting(self):
        response_asc = self.client.get(f"{reverse('booking:test_catalog')}?sort=price_asc")
        content_asc = response_asc.content.decode('utf-8')
        self.assertTrue(content_asc.find("Blood Sugar") < content_asc.find("Urine Culture"))


class StaffCSVExportTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(username="adminstaff", password="Password123!", is_staff=True)
        self.regular_user = User.objects.create_user(username="regularuser", password="Password123!")

    def test_regular_user_cannot_export_csv(self):
        self.client.login(username="regularuser", password="Password123!")
        response = self.client.get(reverse('booking:export_bookings_csv'))
        self.assertNotEqual(response.status_code, 200)

    def test_staff_user_export_csv(self):
        self.client.login(username="adminstaff", password="Password123!")
        response = self.client.get(reverse('booking:export_bookings_csv'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
