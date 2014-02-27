import textwrap, os

def generate_mod_wsgi_config():
    user = 'git' # TODO: conf value?
    group = 'git' # TODO: conf value?
    venv = os.getenv('VIRTUAL_ENV', None)
    wsgi_dir = os.path.dirname(__file__)
    wsgi = os.path.join(wsgi_dir, 'gitzebo.wsgi')

    output = []
    output += [textwrap.dedent("""
        # Write to a usable prefix...
        WSGISocketPrefix /var/run/wsgi
        """)]
    if venv:
        output += [textwrap.dedent("""
            # Set up virtualenv
            WSGIPythonHome {venv}
            """).format(venv=venv)]
    output += [textwrap.dedent("""
        # Make sure authentication information is passed
        # request.auth is None otherwise.
        WSGIPassAuthorization On
        
        # Set permissions for gitzebo dir
        <Directory {wsgi_dir}>
            Order allow,deny
            Allow from all
        </Directory>
        
        # Set up WSGI Alias
        WSGIDaemonProcess gitzebo user={user} group={group}
        WSGIProcessGroup gitzebo
        WSGIScriptAlias / {wsgi}
        """).format(
            wsgi=wsgi,
            wsgi_dir=wsgi_dir,
            user=user,
            group=group
        )]

    return "\n".join(output)
