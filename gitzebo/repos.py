#!/usr/bin/env python
"""
Module to manipulate git repositories and their hooks.
"""

# We'll need the schema module to play with the database.
from schema import db
import schema
repos = schema.get_table('repositories')
repo_acls = schema.get_table('repository_acls')
users = schema.get_table('users') # repository ACLs refer to users

repo_root = "/opt/git"
base_hook_dir = 'default_hooks' # name of directory from which we grab hook code

# We'll also need some SQLAlchemy functionality to write queries.
from sqlalchemy.sql import select
from sqlalchemy.sql.expression import and_, or_, join, outerjoin, subquery

# We do a lot of path manipulation...
import os

def format_name(name):
    # append .git extension if missing; it seems to be a convention
    if len(name) < 4 or name[-4:] != ".git":
        name += ".git"

    # make sure the path derives from the root
    # TODO: we need canonicalization here to prevent traversal attacks
    path = os.path.join(repo_root, name)

    return (name, path)

def get_repo(name):
    s = select([repos]).where(repos.c.repository_name == name)
    result = db.execute(s)
    return result.fetchone()

def get_repo_by_id(id):
    s = select([repos]).where(repos.c.repository_id == id)
    result = db.execute(s)
    return result.fetchone()

def delete_repo_by_id(id):
    repo = get_repo_by_id(id)
    if not repo:
        raise KeyError("Invalid repository ID")
    (name, path) = format_name(repo['repository_name'])
    import shutil
    shutil.rmtree(path)
    # TODO: Shouldn't these two be in the same transaction?
    #       How do we implement transactions in SQLAlchemy?
    s = repos.delete().where(repos.c.repository_id == id)
    result = db.execute(s)
    s = repo_acls.delete().where(repo_acls.c.repository_id == id)
    result = db.execute(s)
    # TODO: return a value in this function?

def get_repos_for_user(user_id):
    columns = repos.c + [repo_acls.c.is_owner, repo_acls.c.can_read,
        repo_acls.c.can_write, repo_acls.c.can_rewind,
        repo_acls.c.can_create_tag, repo_acls.c.can_modify_tag]
    s = select(columns).where(
        (repo_acls.c.repository_id == repos.c.repository_id)
        & (repo_acls.c.user_id == user_id)
        & (repo_acls.c.can_read | repo_acls.c.is_owner))
    return db.execute(s).fetchall()

# TODO: Everything related to repository ACLs will not scale with user count.
#       Eventually, we need to figure out some sort of pagination here.
def get_repo_acls(repo_id, user_id=None):
    """
    Get a list of the permissions each user has on this repo.

    If user_id is provided, the returned list will only contain that user's
    ACLs.
    """
    # branch if filtering by user ID
    user_clause = True
    if user_id:
        user_clause = users.c.user_id == user_id

    
    sq = (
        select([repo_acls])
        .where(repo_acls.c.repository_id == repo_id)
        .alias()
    )
    columns = [c for c in users.c]
    columns += [c for c in sq.c if c not in [sq.c.user_id]]
    s = (
        users.outerjoin(sq, (users.c.user_id == sq.c.user_id))
        .select(user_clause)
        .with_only_columns(columns)
    )
    result = db.execute(s)
    return result.fetchall()

def update_repo_acls(repo_id, user_id, **kwargs):
    # check if we need to do an update
    # TODO: This behavior is ANYTHING except transaction-safe...
    s = select([repo_acls]).where(
        (repo_acls.c.repository_id == repo_id)
        & (repo_acls.c.user_id == user_id))
    acl = db.execute(s).fetchone()
    if not acl:
        s = repo_acls.insert().values(
            repository_id=repo_id,
            user_id=user_id,
            **kwargs)
    else:
        s = repo_acls.update().values(**kwargs).where(
            (repo_acls.c.repository_id == repo_id)
            & (repo_acls.c.user_id == user_id)
        )
    db.execute(s)

def update_hooks(name):
    (name, path) = format_name(name)
    gitzebo_dir = os.path.dirname(os.path.abspath(__file__))
    base_hook_path = os.path.join(gitzebo_dir, base_hook_dir)
    from glob import glob
    from shutil import copyfile, copymode
    from tempfile import NamedTemporaryFile
    from textwrap import dedent
    for source_path in glob(os.path.join(base_hook_path, '*')):
        basename = os.path.basename(source_path)

        # Perform inline edits to insure that our environment is
        # reproduced when git invokes the hooks.  These hacks insure that
        # a virtualenv installation of gitzebo won't choke when hooks
        # execute -- which helps, as virtualenv is the suggested deployment
        # path.
        temp_file = NamedTemporaryFile(mode='w')
        with open(source_path, 'r') as source_file:
            for line in source_file:
                # TODO: Doesn't the VIRTUAL_ENV variable get passed by the
                #       wrapper?  If so, we likely don't need any of this
                #       hacky silliness anymore...
                if line.strip() == '# INSERT ENVIRONMENT HACKS HERE':
                    print "Adding environment hacks"
                    virtualenv = os.getenv('VIRTUAL_ENV', None)
                    if virtualenv:
                        activate_path = os.path.join(
                            virtualenv, 'bin', 'activate_this.py')
                        environment_lines = """\
                            # Activate virtualenv
                            activator = '{0}'
                            execfile(activator, dict(__file__=activator))
                            """.format(activate_path)
                        # Prevent wild indenting from triple-quotes
                        environment_lines = dedent(environment_lines)
                        temp_file.write(environment_lines)
                        print "Setting virtualenv to " + virtualenv
                    else:
                        print "No special environment detected;",
                        print "not writing environment hacks."
                else:
                    temp_file.write(line)
        temp_file.flush()

        # Copy our modified hook over.  Moving might screw up the
        # temp file's removal when it shifts out of scope.
        target_path = os.path.join(path, 'hooks', basename)
        print source_path
        print " ->", temp_file.name, "(for editing atomically)"
        print " ->", target_path
        # Copy the contents of the temp file...
        copyfile(temp_file.name, target_path)
        # ... but the mode of the source file; otherwise the hooks don't tend
        # to be executable.
        copymode(source_path, target_path)

# Creating a new repository
def create_repo(name, owner_id):
    (name, path) = format_name(name)

    # TODO: a synchronization problem exists here when:
    #    - the repository already exists, but doesn't appear in the DB
    #    - the repository is missing, but appears in the DB
    # If one of these conditions exists, what do we do?
    #
    # For now:
    #    - if it exists in FS but not DB, populate DB
    #    - if it exists in DB but not FS, initialize repo in FS
    #
    # Basically, we naively chug on through and initialize all uninitialized
    # pieces without throwing exceptions.  I'm not sure this is the best
    # policy, as desyncs here may indicate further consistency issues, and
    # ignoring them may hamper debugging.

    # error out if the repository already exists in both FS and DB
    repo = get_repo(name)
    if os.path.isdir(path) and repo:
        raise KeyError("Repository {0} already exists.".format(name))

    # if no FS directory exists, initialize the repo /w subprocess'ed git
    if not os.path.isdir(path):
        # TODO: can we use a native Python library here instead of subprocess?
        # TODO: do we need to insure git is installed properly somehow?
        import subprocess
        cmd = ['git', 'init', '--bare', path]
        proc = subprocess.Popen(
            args=cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        (stdout, stderr) = proc.communicate()
        if proc.returncode != 0:
            raise Exception("git init {0} failed: {1}".format(path, stderr))

    # insert repository row
    s = repos.insert().values(
        repository_name=name
    )
    result = db.execute(s)
    repo_id = result.inserted_primary_key[0]

    # insert default owner ACL
    # TODO: Shouldn't this be in the same transaction as above?!
    #       Theoretically a failure here could be unrecoverable.
    s = repo_acls.insert().values(
        user_id=owner_id,
        repository_id=repo_id,
        is_owner=True,
        can_write=True,
        can_rewind=True,
        can_read=True,
        can_create_tag=True,
        can_modify_tag=True,
    )
    result = db.execute(s)

    # make sure all hooks are up-to-date
    update_hooks(name)

    return repo_id

