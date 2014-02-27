Hacking on gitzebo
==================

If you want to work on gitzebo, you'll want to check out the code.  Deployment
is still similar, but instead of allowing pip to locate the code automatically,
you'll direct it at your local branch.


Using a Development Server
--------------------------

To check out the code, initialize the database, and start a dev server::

    git clone git@github.com:jgilik/gitzebo.git
    cd gitzebo
    virtualenv env
    source env/bin/activate

    # -e means 'editable', meaning changes we make here will take effect
    # without reinstallation being necessary
    #
    # bin/... is unaffected by this option, so reinstall after every
    # change to those utilities
    pip install -e "$PWD"

    gitzebo-schema create
    gitzebo-dev-server

Using a Production Server
-------------------------

If you need to deploy to production from source--say, you've sent a pull
request and I haven't gotten to it yet, here's how I set up my server from
source::

    # create directory if needed
    [[ -d "/opt/gitzebo" ]] || {
        mkdir -p /opt/gitzebo
        chown git: /opt/gitzebo
    }

    # clear away old environment
    rm -rf /opt/gitzebo/env

    # enter git user context
    su - git

    # clone repository
    git clone git@github.com:jgilik/gitzebo.git
    cd gitzebo
    # clean anything accidentally checked in
    ./clean.sh

    # create a venv OUTSIDE of home directory;
    # otherwise httpd user will need read permissions on our home
    virtualenv /opt/gitzebo/env
    source /opt/gitzebo/env/bin/activate
    pip install "$PWD" # note lack of -e
    gitzebo-schema create

    # httpd config
    gitzebo-generate-conf > ~/gitzebo.conf

    # exit out of su session, now root
    exit

    # validate packages installed (CentOS specific)
    rpm -q httpd || yum install -y httpd
    rpm -q mod_wsgi || yum install -y mod_wsgi
    cat ~git/gitzebo.conf > /etc/httpd/conf.d/gitzebo.conf

    # bounce server (there has to be a better way)
    service httpd restart

.. todo:: better way to bounce Apache

Send in Pull Requests!
----------------------

I'm very welcoming of changes--please send them in!

