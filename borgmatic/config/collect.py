import os


def get_default_config_paths(expand_home=True):
    '''
    Based on the value of the XDG_CONFIG_HOME and HOME environment variables, return a list of
    default configuration paths. This includes both system-wide configuration and configuration in
    the current user's home directory.

    Don't expand the home directory ($HOME) if the expand home flag is False.
    '''
    user_config_directory = os.getenv('XDG_CONFIG_HOME') or os.path.join('$HOME', '.config')
    if expand_home:
        user_config_directory = os.path.expandvars(user_config_directory)

    return [
        '/etc/borgmatic/config.yaml',
        '/etc/borgmatic.d',
        '%s/borgmatic/config.yaml' % user_config_directory,
        '%s/borgmatic.d' % user_config_directory,
    ]


def collect_config_filenames(config_paths):
    '''
    Given a sequence of config paths, both filenames and directories, resolve that to an iterable
    of files. Accomplish this by listing any given directories looking for contained config files
    (ending with the ".yaml" or ".yml" extension). This is non-recursive, so any directories within the given
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

        if not os.access(path, os.R_OK):
            continue

        for filename in sorted(os.listdir(path)):
            full_filename = os.path.join(path, filename)
            matching_filetype = full_filename.endswith('.yaml') or full_filename.endswith('.yml')
            if matching_filetype and not os.path.isdir(full_filename):
                yield full_filename
