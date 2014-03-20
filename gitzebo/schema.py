#!/usr/bin/env python
import sqlalchemy, os

# DB path is currently rooted in our module directory by default
# TODO: database configuration should be externalized
db_path = os.path.join(os.path.dirname(__file__), 'gitzebo.db')
db = sqlalchemy.create_engine("sqlite:///{0}".format(db_path))
latest_version=1

from sqlalchemy import (Table, Column, MetaData,
    ForeignKey, ColumnDefault,
    Integer, String, Boolean, Text)

def get_metadata(version=latest_version, db=db):
    metadata = MetaData(db)

    schema_version = Table('_schema_version', metadata,
        Column('version', Integer),
    )

    users = Table('users', metadata,
        Column('user_id', Integer, primary_key=True),
        Column('user_name', String, unique=True),
        Column('pass_hash', String),
        Column('pass_salt', String),
        Column('commit_name', String),
        Column('commit_email', String),
        Column('can_create_users', Boolean, ColumnDefault(False)),
        Column('can_create_repositories', Boolean, ColumnDefault(False)),
    )

    keys = Table('keys', metadata,
        Column('key_id', Integer, primary_key=True),
        Column('user_id', Integer, ForeignKey('users.user_id')),
        Column('name', String),
        Column('public_key', Text),
        # TODO: public_key should be unique, but TEXT columns can't be (I think)
        #       verify me maybe?
    )

    repos = Table('repositories', metadata,
        Column('repository_id', Integer, primary_key=True),
        Column('repository_name', String, unique=True),
    )

    repo_acls = Table('repository_acls', metadata,
        Column('user_id', Integer, ForeignKey('users.user_id')),
        Column('repository_id', Integer,
            ForeignKey('repositories.repository_id')),
        Column('is_owner', Boolean, ColumnDefault(False)),
        Column('can_write', Boolean, ColumnDefault(False)),
        Column('can_rewind', Boolean, ColumnDefault(False)),
        Column('can_read', Boolean, ColumnDefault(False)),
        Column('can_create_tag', Boolean, ColumnDefault(False)),
        Column('can_modify_tag', Boolean, ColumnDefault(False)),
    )

    return metadata

def get_table(table, db=db):
    metadata = get_metadata(db=db)
    return metadata.tables[table]

def create_schema(version=latest_version, db=db):
    metadata = get_metadata(version=version, db=db)

    # Insure that our schema versioning table doesn't exist--
    # which also insures that we're not trying to provision over
    # an existing database, as we have an explicit upgrade
    # workflow.
    if metadata.tables['_schema_version'].exists():
        raise Exception("Database already provisioned")

    # Check to see if any tables already exist, which would mean
    # we're attempting to provision a database that contains some
    # other application's data.  If it contained our application's
    # data, the _schema_version table would exist!
    for table in metadata.sorted_tables:
        if table.exists():
            raise Exception("Table already exists: " + table.name)

    # Create all of our tables
    metadata.create_all(db)

    # Populate schema version
    version_table = metadata.tables['_schema_version']
    # TODO: do we need to check for success somehow?
    db.execute(version_table.insert().values(version=version))

    # Create the default admin user
    from users import create_user
    id = create_user('admin', password='admin', commit_email='', can_create_users=True, can_create_repositories=True)

def upgrade_schema(db=db):
    raise Exception("upgrade_schema() not implemented")

# TODO: Fix this so we can destroy older schemas that contain extraneous tables
#       without problems; right now, they would be left dangling unless we
#       upgraded first :o
def destroy_schema(db=db):
    metadata = get_metadata(db=db)
    metadata.drop_all(db)

