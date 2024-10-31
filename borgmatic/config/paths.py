import os


def expand_user_in_path(path):
    '''
    Given a directory path, expand any tildes in it.
    '''
    try:
        return os.path.expanduser(path or '') or None
    except TypeError:
        return None


def get_working_directory(config):  # pragma: no cover
    '''
    Given a configuration dict, get the working directory from it, expanding any tildes.
    '''
    return expand_user_in_path(config.get('working_directory'))


def get_borgmatic_source_directory(config):
    '''
    Given a configuration dict, get the (deprecated) borgmatic source directory, expanding any
    tildes. Defaults to ~/.borgmatic.
    '''
    return expand_user_in_path(config.get('borgmatic_source_directory') or '~/.borgmatic')


def get_borgmatic_runtime_directory(config):
    '''
    Given a configuration dict, get the borgmatic runtime directory used for storing temporary
    runtime data like streaming database dumps and bootstrap metadata. Defaults to the
    "borgmatic_source_directory" value (deprecated) or $XDG_RUNTIME_DIR/borgmatic or
    /var/run/$UID/borgmatic.
    '''
    return expand_user_in_path(
        config.get('borgmatic_runtime_directory')
        or config.get('borgmatic_source_directory')
        or os.path.join(
            os.environ.get(
                'XDG_RUNTIME_DIR',
                f'/var/run/{os.getuid()}',
            ),
            'borgmatic',
        )
    )


def get_borgmatic_state_directory(config):
    '''
    Given a configuration dict, get the borgmatic state directory used for storing borgmatic state
    files like records of when checks last ran. Defaults to the "borgmatic_source_directory" value
    (deprecated) or $XDG_STATE_HOME/borgmatic or ~/.local/state/borgmatic.
    '''
    return expand_user_in_path(
        config.get('borgmatic_state_directory')
        or config.get('borgmatic_source_directory')
        or os.path.join(
            os.environ.get(
                'XDG_STATE_HOME',
                '~/.local/state',
            ),
            'borgmatic',
        )
    )
