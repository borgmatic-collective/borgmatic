import os


def get_default_config_paths():
    '''
    Based on the value of the XDG_CONFIG_HOME and HOME environment variables, return a list of
    default configuration paths. This includes both system-wide configuration and configuration in
    the current user's home directory.
    '''
    user_config_directory = os.getenv('XDG_CONFIG_HOME') or os.path.expandvars(
        os.path.join('$HOME', '.config')
    )

    return [
        '/etc/borgmatic/config.yaml',
        '/etc/borgmatic.d',
        '%s/borgmatic/config.yaml' % user_config_directory,
    ]


def collect_config_filenames(config_paths):
    '''
    Given a sequence of config paths, both filenames and directories, resolve that to an iterable
    of files. Accomplish this by listing any given directories looking for contained config files
    (ending with the ".yaml" extension). This is non-recursive, so any directories within the given
    directories are ignored.

    Return paths even if they don't exist on disk, so the user can find out about missing
    configuration paths. However, skip a default config path if it's missing, so the user doesn't
    have to create a default config path unless they need it.
    '''
    real_default_config_paths = set(map(os.path.realpath, get_default_config_paths()))

    for path in config_paths:
        exists = os.path.exists(path)

        if os.path.realpath(path) in real_default_config_paths and not exists:
            continue

        if not os.path.isdir(path) or not exists:
            yield path
            continue

        for filename in sorted(os.listdir(path)):
            full_filename = os.path.join(path, filename)
            if full_filename.endswith('.yaml') and not os.path.isdir(full_filename):
                yield full_filename
