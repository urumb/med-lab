"""
WSGI config for medical_lab_system project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_lab_system.settings')
application = get_wsgi_application()
