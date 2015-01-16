import os
import site

os.environ.setdefault('CELERY_LOADER', 'django')
# NOTE: you can also set DJANGO_SETTINGS_MODULE in your environment to override
# the default value in manage.py

# Add the app dir to the python path so we can import manage.
wsgidir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(wsgidir, '../')))

# Activate virtualenv
activate_env = os.path.abspath(os.path.join(wsgidir, "../virtualenv/bin/activate_this.py"))
execfile(activate_env, dict(__file__=activate_env))

# Import for side-effects: set-up
import manage

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

# vim: ft=python
