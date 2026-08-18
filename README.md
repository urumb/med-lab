# Medical Lab Management System

[![CI Workflow](https://github.com/urumb/med-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/urumb/med-lab/actions)
[![Django](https://img.shields.io/badge/Django-5.2.5-092E20?style=flat&logo=django)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-quality Django web application for managing medical laboratory diagnostic test bookings, patient accounts, test catalogs, and staff operations. Designed with modern healthcare UX principles, robust database constraints, and secure role-based authorization.

---

## 🚀 Live Demo

- **Live Deployed App**: [https://med-lab-mdps.onrender.com](https://med-lab-mdps.onrender.com)
- **Demo Staff Credentials**: Username `admin` | Password `admin123`
- **Demo Patient Credentials**: Username `john_doe` | Password `patient123`

---

## ✨ Features

### 🩺 Patient Experience & Portal
- **Interactive Test Catalog**: Filter tests by specialized categories (Hematology, Biochemistry, Cardiology, etc.), search by test code or keyword, and review preparation guidelines.
- **Online Appointment Booking**: Select preferred diagnostic tests, choose available date and time slots within operational hours (8:00 AM - 8:00 PM), and receive instant confirmations with unique reference numbers (`LAB-YYYYMMDD-XXXX`).
- **Patient Dashboard**: Authenticated portal showing upcoming appointments, historical test records, status progression badges, and account profile controls.
- **Booking Self-Service**: Track booking status progression and cancel eligible appointments prior to sample processing.

### 🔬 Staff & Administrative Management
- **Laboratory Operations Dashboard**: Real-time staff dashboard displaying KPI stats (total patients, revenue, today's schedule, pending approvals).
- **Status Workflow Pipeline**: Manage sample collection lifecycle (`Pending` → `Confirmed` → `Sample Collected` → `Processing` → `Completed`).
- **Search & Filter Controls**: Filter appointments by status, scheduled date, patient phone number, or booking reference code.
- **Django Admin Customization**: Enhanced Django admin interface with quick action shortcuts, prefetched relations, and date hierarchy breakdown.

---

## ⚙️ Architecture & Tech Stack

- **Backend**: Django 5.2.5 (Python 3.12)
- **Database**: PostgreSQL (Production) / SQLite3 (Local Development)
- **Static File Serving**: WhiteNoise with Brotli compression
- **Frontend**: Responsive Bootstrap 5, Bootstrap Icons, HTML5, AJAX
- **Configuration**: Decoupled environment settings (`python-decouple`, `dj-database-url`)
- **Deployment**: Render Web Services with automated `build.sh` pipeline

---

## 📁 Repository Structure

```text
├── booking/                    # Main Django Application
│   ├── management/commands/    # Management commands (seed_data.py)
│   ├── migrations/             # Database migration files
│   ├── templates/booking/      # UI Templates (base, home, catalog, dashboard, etc.)
│   ├── tests/                  # Automated unit and view test suite
│   ├── admin.py                # Staff Django admin customization
│   ├── forms.py                # Django Forms & validation logic
│   ├── models.py               # Data models (Category, Patient, Test, Booking)
│   ├── urls.py                 # Application URL Routing
│   └── views.py                # View controllers & API endpoints
├── medical_lab_system/         # Django Project Configuration
│   ├── settings.py             # Settings with env variable handling
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py                 # WSGI entrypoint
├── .github/workflows/          # GitHub Actions CI Workflow
├── .env.example                # Sample environment variables configuration
├── build.sh                    # Render production build script
├── manage.py                   # Django CLI tool
├── README.md                   # Comprehensive project documentation
├── render.yaml                 # Render Infrastructure-as-Code spec
└── requirements.txt            # Python dependencies
```

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- Python 3.10 or higher
- Git

### 2. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/urumb/med-lab.git
cd med-lab

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 5. Apply Migrations & Seed Demo Data
```bash
python manage.py migrate
python manage.py seed_data
```

### 6. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 🧪 Running Tests

Run the full automated test suite:
```bash
python manage.py test
```

Run Django system checks:
```bash
python manage.py check
```

---

## 🌐 Production Deployment (Render)

The project includes `render.yaml` and `build.sh` ready for 1-click deployment on Render.

**Environment Variables Required in Production:**
- `SECRET_KEY`: Long random secret string
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: `.onrender.com,yourdomain.com`
- `DATABASE_URL`: PostgreSQL connection string

---

## 📄 License

Distributed under the [MIT License](LICENSE).
