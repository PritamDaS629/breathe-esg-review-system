import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'breathe.settings')

from django.core.wsgi import get_wsgi_application

app = get_wsgi_application()