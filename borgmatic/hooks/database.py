import os


def make_database_dump_filename(dump_path, name, hostname=None):
    '''
    Based on the given dump directory path, database name, and hostname, return a filename to use
    for the database dump. The hostname defaults to localhost.

    Raise ValueError if the database name is invalid.
    '''
    if os.path.sep in name:
        raise ValueError('Invalid database name {}'.format(name))

    return os.path.join(os.path.expanduser(dump_path), hostname or 'localhost', name)
