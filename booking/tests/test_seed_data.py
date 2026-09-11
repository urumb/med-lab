from django.test import TestCase, Client
from django.urls import reverse
from django.core.management import call_command
from django.contrib.auth.models import User
from booking.models import Category, Test, Patient, Booking


class SeedDataCommandTestCase(TestCase):
    """Regression tests for the seed_data management command used to
    populate a fresh production database on deploy."""

    def test_seed_data_creates_expected_catalog(self):
        call_command('seed_data')
        self.assertEqual(Category.objects.count(), 5)
        self.assertEqual(Test.objects.count(), 6)
        self.assertTrue(Category.objects.filter(slug='hematology').exists())
        self.assertTrue(Test.objects.filter(test_name='Complete Blood Count (CBC) with Differential').exists())
        self.assertTrue(User.objects.filter(username='admin', is_staff=True, is_superuser=True).exists())

    def test_seed_data_is_idempotent(self):
        call_command('seed_data')
        call_command('seed_data')

        self.assertEqual(Category.objects.count(), 5)
        self.assertEqual(Test.objects.count(), 6)
        self.assertEqual(User.objects.filter(username='admin').count(), 1)
        self.assertEqual(Patient.objects.count(), 3)
        self.assertEqual(Booking.objects.count(), 3)

    def test_seed_data_does_not_overwrite_existing_data(self):
        call_command('seed_data')

        category = Category.objects.get(slug='hematology')
        category.description = 'Custom description edited by staff'
        category.save()

        call_command('seed_data')

        category.refresh_from_db()
        self.assertEqual(category.description, 'Custom description edited by staff')


class SeededHomepageAndCatalogTestCase(TestCase):
    """Confirms the homepage and catalog render database-backed data,
    rather than falling back to empty states, once seeded."""

    def setUp(self):
        self.client = Client()
        call_command('seed_data')

    def test_homepage_displays_seeded_categories(self):
        response = self.client.get(reverse('booking:home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'No categories configured yet.')
        self.assertContains(response, 'Hematology &amp; Blood Studies')

    def test_homepage_displays_seeded_active_tests(self):
        response = self.client.get(reverse('booking:home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'No active tests available at the moment.')
        self.assertContains(response, 'Complete Blood Count (CBC) with Differential')

    def test_catalog_displays_seeded_tests(self):
        response = self.client.get(reverse('booking:test_catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Lipid Profile &amp; Cardiovascular Risk')

    def test_inactive_test_hidden_from_homepage_and_catalog(self):
        inactive_test = Test.objects.get(code='MIC-URI-01')
        inactive_test.is_active = False
        inactive_test.save()

        home_response = self.client.get(reverse('booking:home'))
        self.assertNotContains(home_response, inactive_test.test_name)

        catalog_response = self.client.get(reverse('booking:test_catalog'))
        self.assertNotContains(catalog_response, inactive_test.test_name)

    def test_inactive_test_detail_not_publicly_accessible(self):
        inactive_test = Test.objects.get(code='MIC-URI-01')
        inactive_test.is_active = False
        inactive_test.save()

        response = self.client.get(reverse('booking:test_detail', args=[inactive_test.id]))
        self.assertEqual(response.status_code, 404)
