import os


def get_working_directory(config):
    '''
    Given a configuration dict, get the working directory from it, first expanding any tildes.
    '''
    try:
        return os.path.expanduser(config.get('working_directory', '')) or None
    except TypeError:
        return None
