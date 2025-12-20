"""
Конфигурация WSGI для проекта publications.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'publications.settings')

application = get_wsgi_application()
