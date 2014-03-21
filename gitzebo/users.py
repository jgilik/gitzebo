#!/usr/bin/env python
# We'll need the schema module to play with the database.
from schema import db
import schema
users = schema.get_table('users')
repo_acls = schema.get_table('repository_acls')

# We'll also need some SQLAlchemy functionality to write queries.
from sqlalchemy.sql import select

# We need hashlib to play with password hashes.
import hashlib

# random and string for salt generation
import string, random

def generate_salt(size=16, chars=string.ascii_letters + string.digits):
    """
    Generates a salt according to `this StackOverflow answer
    <http://stackoverflow.com/a/2257449>`_.
    """
    return ''.join(random.choice(chars) for x in range(size))

def hash_password(password, salt):
    """
    Salts and hashes the password, returning hex-encoded string of the
    SHA256 hash.
    """
    return hashlib.sha256(salt + password).hexdigest()

def create_user(name, password, commit_name=None, commit_email=None, can_create_users=False, can_create_repositories=False):
    salt = generate_salt()
    hash = hash_password(password, salt)
    if commit_name is None:
        commit_name = name
    if commit_email is None:
        commit_email = ''
    stmt = users.insert().values(
        user_name=name,
        commit_name=commit_name,
        commit_email=commit_email,
        pass_salt=salt,
        pass_hash=hash,
        can_create_users=can_create_users,
        can_create_repositories=can_create_repositories,
    )
    result = db.execute(stmt)
    return result.inserted_primary_key[0]

def change_password(name, password, old_password=None):
    """
    Changes the target user's password to the password given by
    ``password``.  If ``old_password`` is given but does not match
    the user's current password, a ValueError is raised.
    """
    if not get_user(name):
        raise KeyError("User '{0}' not found".format(name))
    if old_password is not None:
        if not verify_user(name, password):
            raise ValueError("Old password was incorrect.")
    salt = generate_salt()
    hash = hash_password(password, salt)
    db.execute(users
        .update()
        .values(pass_salt=salt, pass_hash=hash)
        .where(users.c.user_name == name))

def delete_user(user_id):
    s = repo_acls.delete().where(repo_acls.c.user_id == user_id)
    result = db.execute(s)
    s = users.delete().where(users.c.user_id == user_id)
    result = db.execute(s)
    # TODO: should do some sort of return here...

def get_user(name):
    s = select([users]).where(users.c.user_name == name)
    result = db.execute(s)
    return result.fetchone()

def get_user_by_id(id):
    s = select([users]).where(users.c.user_id == id)
    result = db.execute(s)
    return result.fetchone()

def get_users():
    s = select([users])
    result = db.execute(s)
    return result.fetchall()

def verify_user(name, password):
    try:
        user = get_user(name)
    except KeyError:
        return None
    if not user:
        return None
    salt = user[users.c.pass_salt]
    correct_hash = user[users.c.pass_hash]
    attempt_hash = hash_password(password, salt)
    if correct_hash != attempt_hash:
        return None
    return user

