#!/usr/bin/env python
# We'll need the schema module to play with the database.
from schema import db
import schema
keys = schema.get_table('keys')
users = schema.get_table('users') # used when generating authorized_keys

# We'll also need some SQLAlchemy functionality to write queries.
from sqlalchemy.sql import select

# os.path and errno are used in rewriting the authorized_keys file
import os, errno

# TODO: We assume RSA keys at the moment.

def validate_key(key):
    """
    Validate that a given string looks like a proper public key.
    """
    # Validate that the string parses
    import base64, binascii
    try:
        base64.decodestring(key)
    except binascii.Error:
        return False

    # Validate the Base64 alphabet described in RFC 3548
    valid_chars = [chr(ord('A') + i) for i in range(26)]
    valid_chars += [chr(ord('a') + i) for i in range(26)]
    valid_chars += [chr(ord('0') + i) for i in range(10)]
    valid_chars += ['+', '/', '=']
    for char in key:
        if char not in valid_chars:
            return False

    # If nothing has bounced, we're as okay as we can imagine
    return True

def create_key(user_id, key, name):
    # validate data
    if not validate_key(key):
        raise ValueError("Invalid public key: '" + key + "'")

    # validate uniqueness
    if get_key_by_key(key):
        raise Exception("Key already exists in database.")

    # insert key
    stmt = keys.insert().values(
        user_id=user_id,
        name=name,
        public_key=key)
    result = db.execute(stmt)

    # insure the filesystem reflects changes and return
    regenerate_authorized_keys()
    return result.inserted_primary_key

def delete_key(key_id):
    # delete it!
    s = keys.delete().where(keys.c.key_id == key_id)
    result = db.execute(s)
    if result.rowcount != 1:
        raise Exception("Deleted {0} rows, expected to delete one.".format(
            result.rowcount))

    # insure the filesystem reflects changes and return
    regenerate_authorized_keys()
    return result.rowcount

def get_key_by_key(key):
    """
    Look up a key by the actual key (reverse lookup).

    Used to enforce uniqueness of keys, so that we don't generate an
    invalid authorized_keys file.
    """
    s = select([keys]).where(keys.c.public_key == key)
    result = db.execute(s)
    return result.fetchone()

def get_key_by_id(key_id):
    s = select([keys]).where(keys.c.key_id == key_id)
    result = db.execute(s)
    return result.fetchone()

def get_keys(user_id):
    s = select([keys]).where(keys.c.user_id == user_id)
    result = db.execute(s)
    return result.fetchall()

def regenerate_authorized_keys():
    # do as much validaton as possible
    home = os.getenv('HOME', None)
    if home is None:
        raise ValueError("HOME environment variable should be set!")

    # perform SQL query
    s = select([keys, users]).where(keys.c.user_id == users.c.user_id)
    result = db.execute(s)

    # attempt to locate our SSH wrapper
    from distutils.spawn import find_executable
    wrapper_path = find_executable('gitzebo-ssh-wrapper')

    # make sure ssh directory exists
    target_dir = os.path.join(home, '.ssh')
    try:
        os.makedirs(target_dir)
        os.chmod(target_dir, 0700)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(target_dir):
            pass
        else:
            raise

    # write resultset to file
    target_path = os.path.join(target_dir, 'authorized_keys')
    # TODO: eventually allow for DSA keys, too?
    venv = ''
    venv_dir = os.getenv('VIRTUAL_ENV', None)
    if venv_dir:
        venv = ' VIRTUAL_ENV=' + venv_dir
    with open(target_path, 'w') as f:
        for row in db.execute(s):
            f.write('command="{wrapper} USERNAME={username}{venv}",'
                'no-port-forwarding,'
                'no-X11-forwarding,'
                'no-agent-forwarding,'
                'no-pty'
                ' ssh-rsa {key}\n'.format(
                    wrapper=wrapper_path,
                    username=row['user_name'],
                    key=row['public_key'],
                    venv=venv, # virtualenv spec, if applicable
                )
            )

    # move temporary file into place and return
    # TODO: We should be doing atomic writes here!
    #       Write to a temp file, and then overwrite-move it to the target path.

