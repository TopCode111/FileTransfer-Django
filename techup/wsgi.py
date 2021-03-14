"""
WSGI config for techup project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
import urllib

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'techup.settings')

application = get_wsgi_application()

filename = urllib.parse.quote(filename) 
response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
