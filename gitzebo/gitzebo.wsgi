import sys
import os
import site

# This ugly wrapper exists solely to preserve the VIRTUAL_ENV variable.
# Per: http://ericplumb.com/blog/passing-apache-environment-variables-to-django-via-mod_wsgi.html
#
# Without it, you will wind up without VIRTUAL_ENV settings in your
# .ssh/authorized_keys file, which will prevent logins.
#
# It also activates the virtualenv if the VIRTUAL_ENV setting is set.
def application(environ, start_response):
    for key in ['VIRTUAL_ENV']:
        if key in environ:
            os.environ[key] = environ.get(key)

    venv = environ.get('VIRTUAL_ENV', None)

    # virtualenv inclusion from mod_wsgi documentation
    if venv:
        activate_this = os.path.join(venv, 'bin', 'activate_this.py')
        execfile(activate_this, dict(__file__=activate_this))

    from gitzebo.flask_app import app
    return app(environ, start_response)

