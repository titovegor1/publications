"""
Конфигурация ASGI для проекта publications.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'publications.settings')

application = get_asgi_application()
