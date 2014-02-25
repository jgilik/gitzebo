#!/usr/bin/env python
from flask import Flask, render_template
app = Flask(__name__)

from schema import db

import flask
from flask import request, redirect, abort

#######################
# Authentication code #
#######################
# Pulled from http://flask.pocoo.org/snippets/31/
# TODO: POSSIBLY ready to refactor out
from functools import wraps
from flask import request, Response
from users import verify_user

def authenticate():
    """
    Requests authentication credentials from user.
    """
    return Response('You must log in to access this functionality.',
        401, {'WWW-Authenticate': 'Basic realm="Gitzebo"'})

@app.before_request
def auth_helper():
    request.user = None
    auth = request.authorization
    if not auth:
        return
    user = verify_user(auth.username, auth.password)
    if not user:
        return
    request.user = user
    return

def requires_auth(f):
    """
    Decorates a Flask call to require authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.user:
            return authenticate()
        return f(*args, **kwargs)
    return decorated

########################
# CORE WEB APPLICATION #
########################
import users, repos, keys

@app.route("/")
def home():
    return redirect(url_for('list_repos'))

#####################
# USER MANIPULATION #
#####################

@app.route("/users")
@requires_auth
def list_users():
    # return list of users
    userlist = users.get_users()
    return render_template('users.html', userlist=userlist)

@app.route("/users/<int:id>")
@requires_auth
def user_details(id):
    user = users.get_user_by_id(id)
    return render_template('user_details.html', user=user)

@app.route("/users/add", methods=['POST'])
@requires_auth
def add_user():
    if not request.user['can_create_users']:
        raise Exception("Permission denied; user cannot modify users.")
    for key in ['user_name', 'user_password', 'commit_name', 'commit_email']:
        if key not in request.form or len(request.form[key]) < 1:
            raise Exception("User creation form requires field '{0}'"
                .format(key))
    user_name = request.form['user_name']
    password = request.form['user_password']
    commit_name = request.form['commit_name']
    commit_email = request.form['commit_email']
    user_id = users.create_user(
        user_name,
        password=password,
        commit_name=commit_name,
        commit_email=commit_email)
    # TODO: redirect to user details?
    return redirect(url_for('list_users'))

@app.route("/users/delete/<int:id>")
@requires_auth
def delete_user(id):
    if not request.user['can_create_users']:
        raise Exception("Permission denied; user cannot modify users.")
    users.delete_user(id)
    return redirect(url_for('list_users'))

####################
# KEY MANIPULATION #
####################

@app.route("/keys")
@requires_auth
def list_keys():
    keylist = keys.get_keys(request.user['user_id'])
    return render_template('keys.html', keylist=keylist)

@app.route("/keys/add", methods=['POST'])
@requires_auth
def add_key():
    # create_key(user_id, key, name):
    keys.create_key(
        user_id=request.user['user_id'],
        key=request.form['key'].strip(),
        name=request.form['key_name'].strip(),
    )
    return redirect(url_for('list_keys'))

@app.route("/keys/delete/<int:id>")
@requires_auth
def delete_key(id):
    key = keys.get_key_by_id(id)
    if not key:
        raise Exception("Key does not exist!")
    if key['user_id'] != request.user['user_id']:
        raise Exception("Permission denied: you don't own this key.")
    keys.delete_key(id)
    return redirect(url_for('list_keys'))


###########################
# REPOSITORY MANIPULATION #
###########################

@app.route("/repos")
@requires_auth
def list_repos():
    repolist = repos.get_repos_for_user(request.user['user_id'])
    return render_template('repos.html', repolist=repolist)

def assert_repo_permission(repo_id, permission):
    user_acls = repos.get_repo_acls(
        repo_id=repo_id,
        user_id=request.user['user_id'])

    user_acls = user_acls[0]

    if not user_acls[permission]:
        raise Exception("Permission denied; user {0} lacks {1} permissions"
            " for the repository with ID {2}".format(
                request.user['user_name'],
                permission,
                repo_id))

def render_repo_details(id, template):
    repo = repos.get_repo_by_id(id)
    repo_acls = repos.get_repo_acls(repo_id=repo['repository_id'])
    user_id = request.user['user_id']
    user_acls = [a for a in repo_acls if a['user_id'] == user_id][0]

    # get our hostname for the git clone example
    import urlparse
    parsed_url = urlparse.urlparse(request.url)

    return render_template(template,
        repo=repo,
        repo_acls=repo_acls,
        hostname=parsed_url.hostname,
        user_acls=user_acls)

@app.route("/repos/details/<int:id>")
@requires_auth
def repo_details(id):
    assert_repo_permission(id, 'can_read')
    return render_repo_details(id, 'repo_details.html')

@app.route("/repos/edit/<int:id>", methods=['GET', 'POST'])
@requires_auth
def edit_repo(id):
    assert_repo_permission(id, 'is_owner')

    if request.method == 'GET':
        return render_repo_details(id, 'repo_edit.html')

    # commit changes
    permissions = ['is_owner', 'can_read', 'can_write', 'can_rewind',
        'can_create_tag', 'can_modify_tag']
    for user in users.get_users():
        user_permissions = {}
        if 'exists_' + str(user['user_id']) not in request.form:
            continue
        for permission in permissions:
            name = '{0}_{1}'.format(permission, user['user_id'])
            value = name in request.form
            user_permissions[permission] = value
        repos.update_repo_acls(
            repo_id=id,
            user_id=user['user_id'],
            **user_permissions
        )

    return redirect(url_for('edit_repo', id=id))

# TODO: Pretty much all of our administration tasks are vulnerable to CSRF.
@app.route("/repos/delete/<int:id>")
@requires_auth
def delete_repo(id):
    repo = repos.get_repo_by_id(id)
    repo_acls = repos.get_repo_acls(
        repo_id=repo['repository_id'],
        user_id=request.user['user_id'])
    if not repo_acls or len(repo_acls) < 1 or not repo_acls[0]['is_owner']:
        raise Exception("Permission denied; user doesn't own this repository.")
    repos.delete_repo_by_id(id)
    return redirect(url_for('list_repos'))

@app.route("/repos/add", methods=['POST'])
@requires_auth
def add_repo():
    if not request.user['can_create_repositories']:
        raise Exception("Permission denied; user cannot create repositories.")
    name = request.form['repository_name']
    # TODO: externalize minimum repo name length
    if not name or len(name) <= 3:
        raise Exception("Repository name is too short.")
    id = repos.create_repo(name=name, owner_id=request.user['user_id'])
    return redirect(url_for('repo_details', id=id))

####################
# TEMPLATE HELPERS #
####################
@app.template_global()
def url_for(target, *args, **kwargs):
    return flask.url_for(target, *args, **kwargs)

