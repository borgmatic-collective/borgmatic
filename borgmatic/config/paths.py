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
    runtime data like streaming database dumps and bootstrap metadata. Defaults to
    $XDG_RUNTIME_DIR/./borgmatic or $TMPDIR/./borgmatic or $TEMP/./borgmatic or
    /run/user/$UID/./borgmatic.

    The "/./" is taking advantage of a Borg feature such that the part of the path before the "/./"
    does not get stored in the file path within an archive. That way, the path of the runtime
    directory can change without leaving database dumps within an archive inaccessible.
    '''
    return expand_user_in_path(
        os.path.join(
            config.get('user_runtime_directory')
            or os.environ.get('XDG_RUNTIME_DIR')
            or os.environ.get('TMPDIR')
            or os.environ.get('TEMP')
            or f'/run/user/{os.getuid()}',
            '.',
            'borgmatic',
        )
    )


def get_borgmatic_state_directory(config):
    '''
    Given a configuration dict, get the borgmatic state directory used for storing borgmatic state
    files like records of when checks last ran. Defaults to $XDG_STATE_HOME/borgmatic or
    ~/.local/state/./borgmatic.
    '''
    return expand_user_in_path(
        os.path.join(
            config.get('user_state_directory')
            or os.environ.get(
                'XDG_STATE_HOME',
                '~/.local/state',
            ),
            'borgmatic',
        )
    )
