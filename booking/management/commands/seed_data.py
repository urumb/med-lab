import random
from datetime import date, timedelta, time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from booking.models import Category, Test, Patient, Booking


class Command(BaseCommand):
    help = 'Seeds database with realistic demo categories, tests, patients, and bookings'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seed process...'))

        # 1. Categories
        categories_data = [
            {'name': 'Hematology & Blood Studies', 'slug': 'hematology', 'icon': 'bi-droplet-half', 'description': 'Complete blood cell counts, coagulation factors, and blood morphology.'},
            {'name': 'Biochemistry & Metabolic', 'slug': 'biochemistry', 'icon': 'bi-activity', 'description': 'Glucose levels, renal panel, liver function, and electrolyte balances.'},
            {'name': 'Thyroid & Hormonal Panels', 'slug': 'endocrinology', 'icon': 'bi-heart-pulse', 'description': 'Thyroid stimulation hormones, cortisol, reproductive panel, and metabolic markers.'},
            {'name': 'Cardiac Diagnostic Markers', 'slug': 'cardiology', 'icon': 'bi-heart', 'description': 'Lipid panels, high-sensitivity CRP, troponin, and cardiovascular risks.'},
            {'name': 'Pathology & Microbiology', 'slug': 'microbiology', 'icon': 'bi-virus', 'description': 'Urine analysis, bacterial cultures, parasite testing, and infectious disease panels.'},
        ]

        created_categories = {}
        for cat in categories_data:
            c, _ = Category.objects.get_or_create(
                slug=cat['slug'],
                defaults={'name': cat['name'], 'icon': cat['icon'], 'description': cat['description']}
            )
            created_categories[cat['slug']] = c

        # 2. Medical Tests
        tests_data = [
            {
                'category': created_categories['hematology'],
                'test_name': 'Complete Blood Count (CBC) with Differential',
                'code': 'HEM-CBC-01',
                'description': 'Measures red and white blood cells, hemoglobin, hematocrit, and platelets to evaluate overall health and detect disorders like anemia or infection.',
                'preparation_instructions': 'No fasting required. Stay hydrated before sample collection.',
                'price': 450.00,
                'turnaround_time': '12 Hours',
                'duration_hours': 1,
            },
            {
                'category': created_categories['biochemistry'],
                'test_name': 'Comprehensive Metabolic Panel (CMP)',
                'code': 'BIO-CMP-02',
                'description': 'Evaluates kidney function, liver health, electrolyte balance, blood sugar levels, and plasma protein status.',
                'preparation_instructions': 'Requires 8-12 hours of overnight fasting prior to blood draw.',
                'price': 850.00,
                'turnaround_time': '24 Hours',
                'duration_hours': 1,
            },
            {
                'category': created_categories['biochemistry'],
                'test_name': 'HbA1c Glycated Hemoglobin',
                'code': 'BIO-HBA1C',
                'description': 'Provides an average of your blood sugar levels over the past 2 to 3 months to diagnose and manage diabetes.',
                'preparation_instructions': 'No fasting required for HbA1c test.',
                'price': 600.00,
                'turnaround_time': '12 Hours',
                'duration_hours': 1,
            },
            {
                'category': created_categories['cardiology'],
                'test_name': 'Lipid Profile & Cardiovascular Risk',
                'code': 'CARD-LIP-01',
                'description': 'Measures Total Cholesterol, HDL, LDL, VLDL, and Triglycerides to assess heart disease risk factors.',
                'preparation_instructions': 'Strict 10-12 hours fasting required. Water is allowed.',
                'price': 750.00,
                'turnaround_time': '24 Hours',
                'duration_hours': 1,
            },
            {
                'category': created_categories['endocrinology'],
                'test_name': 'Thyroid Profile Total (T3, T4, TSH)',
                'code': 'THY-TOT-03',
                'description': 'Assesses overall thyroid gland function and helps diagnose hyperthyroidism or hypothyroidism.',
                'preparation_instructions': 'Morning sample collection recommended. Inform staff if taking thyroid medication.',
                'price': 900.00,
                'turnaround_time': '24 Hours',
                'duration_hours': 1,
            },
            {
                'category': created_categories['microbiology'],
                'test_name': 'Complete Urinalysis & Routine Microscopy',
                'code': 'MIC-URI-01',
                'description': 'Screening test for metabolic disorders, urinary tract infections (UTI), and kidney disease.',
                'preparation_instructions': 'First morning clean-catch midstream urine sample required in sterile container.',
                'price': 300.00,
                'turnaround_time': '6 Hours',
                'duration_hours': 1,
            },
        ]

        created_tests = []
        for t in tests_data:
            test_obj, _ = Test.objects.get_or_create(
                test_name=t['test_name'],
                defaults=t
            )
            created_tests.append(test_obj)

        # 3. Superuser / Staff Account
        staff_user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@medlab.org', 'is_staff': True, 'is_superuser': True})
        if created:
            staff_user.set_password('admin123')
            staff_user.save()

        # 4. Demo Patients
        patients_info = [
            {'username': 'john_doe', 'name': 'John Doe', 'age': 38, 'gender': 'M', 'phone': '+19876543210', 'email': 'john.doe@example.com', 'address': '123 Health Ave, Suite 4B, New York, NY'},
            {'username': 'jane_smith', 'name': 'Jane Smith', 'age': 29, 'gender': 'F', 'phone': '+19876543211', 'email': 'jane.smith@example.com', 'address': '456 Medical Parkway, Boston, MA'},
            {'username': 'robert_brown', 'name': 'Robert Brown', 'age': 54, 'gender': 'M', 'phone': '+19876543212', 'email': 'robert.brown@example.com', 'address': '789 Oak Ridge Dr, Chicago, IL'},
        ]

        created_patients = []
        for pdata in patients_info:
            u, user_created = User.objects.get_or_create(username=pdata['username'], defaults={'email': pdata['email'], 'first_name': pdata['name'].split()[0], 'last_name': pdata['name'].split()[1]})
            if user_created:
                u.set_password('patient123')
                u.save()

            patient_obj, _ = Patient.objects.get_or_create(
                email=pdata['email'],
                defaults={
                    'user': u,
                    'name': pdata['name'],
                    'age': pdata['age'],
                    'gender': pdata['gender'],
                    'phone': pdata['phone'],
                    'address': pdata['address']
                }
            )
            created_patients.append(patient_obj)

        # 5. Bookings
        today = date.today()
        statuses = [Booking.STATUS_PENDING, Booking.STATUS_CONFIRMED, Booking.STATUS_COMPLETED]
        sample_times = [time(8, 30), time(10, 0), time(11, 30), time(14, 0), time(16, 30)]

        for i, patient in enumerate(created_patients):
            test = created_tests[i % len(created_tests)]
            booking_date = today + timedelta(days=i + 1)
            booking_time = sample_times[i % len(sample_times)]
            status = statuses[i % len(statuses)]

            if not Booking.objects.filter(patient=patient, test=test, booking_date=booking_date).exists():
                Booking.objects.create(
                    patient=patient,
                    test=test,
                    booking_date=booking_date,
                    booking_time=booking_time,
                    status=status,
                    notes=f'Demo automated seed booking #{i+1}'
                )

        self.stdout.write(self.style.SUCCESS('Database successfully seeded with demo categories, tests, patients, and bookings!'))
