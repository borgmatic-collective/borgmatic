import os


DEFAULT_CONFIG_PATHS = ['/etc/borgmatic/config.yaml', '/etc/borgmatic.d']


def collect_config_filenames(config_paths):
    '''
    Given a sequence of config paths, both filenames and directories, resolve that to just an
    iterable of files. Accomplish this by listing any given directories looking for contained config
    files. This is non-recursive, so any directories within the given directories are ignored.

    Return paths even if they don't exist on disk, so the user can find out about missing
    configuration paths. However, skip a default config path if it's missing, so the user doesn't
    have to create a default config path unless they need it.
    '''
    real_default_config_paths = set(map(os.path.realpath, DEFAULT_CONFIG_PATHS))

    for path in config_paths:
        exists = os.path.exists(path)

        if os.path.realpath(path) in real_default_config_paths and not exists:
            continue

        if not os.path.isdir(path) or not exists:
            yield path
            continue

        for filename in os.listdir(path):
            full_filename = os.path.join(path, filename)
            if not os.path.isdir(full_filename):
                yield full_filename
