import logging
import os
import tempfile

logger = logging.getLogger(__name__)


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


TEMPORARY_DIRECTORY_PREFIX = 'borgmatic-'


def replace_temporary_subdirectory_with_glob(
    path, temporary_directory_prefix=TEMPORARY_DIRECTORY_PREFIX
):
    '''
    Given an absolute temporary directory path and an optional temporary directory prefix, look for
    a subdirectory within it starting with the temporary directory prefix (or a default) and replace
    it with an appropriate glob. For instance, given:

        /tmp/borgmatic-aet8kn93/borgmatic

    ... replace it with:

        /tmp/borgmatic-*/borgmatic

    This is useful for finding previous temporary directories from prior borgmatic runs.
    '''
    return os.path.join(
        '/',
        *(
            (
                f'{temporary_directory_prefix}*'
                if subdirectory.startswith(temporary_directory_prefix)
                else subdirectory
            )
            for subdirectory in path.split(os.path.sep)
        ),
    )


class Runtime_directory:
    '''
    A Python context manager for creating and cleaning up the borgmatic runtime directory used for
    storing temporary runtime data like streaming database dumps and bootstrap metadata.

    Example use as a context manager:

        with borgmatic.config.paths.Runtime_directory(config) as borgmatic_runtime_directory:
            do_something_with(borgmatic_runtime_directory)

    For the scope of that "with" statement, the runtime directory is available. Afterwards, it
    automatically gets cleaned up as necessary.
    '''

    def __init__(self, config):
        '''
        Given a configuration dict determine the borgmatic runtime directory, creating a secure,
        temporary directory within it if necessary. Defaults to $XDG_RUNTIME_DIR/./borgmatic or
        $RUNTIME_DIRECTORY/./borgmatic or $TMPDIR/borgmatic-[random]/./borgmatic or
        $TEMP/borgmatic-[random]/./borgmatic or /tmp/borgmatic-[random]/./borgmatic where "[random]"
        is a randomly generated string intended to avoid path collisions.

        If XDG_RUNTIME_DIR or RUNTIME_DIRECTORY is set and already ends in "/borgmatic", then don't
        tack on a second "/borgmatic" path component.

        The "/./" is taking advantage of a Borg feature such that the part of the path before the "/./"
        does not get stored in the file path within an archive. That way, the path of the runtime
        directory can change without leaving database dumps within an archive inaccessible.
        '''
        runtime_directory = (
            config.get('user_runtime_directory')
            or os.environ.get('XDG_RUNTIME_DIR')  # Set by PAM on Linux.
            or os.environ.get('RUNTIME_DIRECTORY')  # Set by systemd if configured.
        )

        if runtime_directory:
            if not runtime_directory.startswith(os.path.sep):
                raise ValueError('The runtime directory must be an absolute path')

            self.temporary_directory = None
        else:
            base_directory = (
                os.environ.get('TMPDIR') or os.environ.get('TEMP') or '/tmp'  # noqa: S108
            )

            if not base_directory.startswith(os.path.sep):
                raise ValueError('The temporary directory must be an absolute path')

            os.makedirs(base_directory, mode=0o700, exist_ok=True)
            self.temporary_directory = tempfile.TemporaryDirectory(
                prefix=TEMPORARY_DIRECTORY_PREFIX,
                dir=base_directory,
            )
            runtime_directory = self.temporary_directory.name

        (base_path, final_directory) = os.path.split(runtime_directory.rstrip(os.path.sep))

        self.runtime_path = expand_user_in_path(
            os.path.join(
                base_path if final_directory == 'borgmatic' else runtime_directory,
                '.',  # Borg 1.4+ "slashdot" hack.
                'borgmatic',
            )
        )
        os.makedirs(self.runtime_path, mode=0o700, exist_ok=True)

        logger.debug(f'Using runtime directory {os.path.normpath(self.runtime_path)}')

    def __enter__(self):
        '''
        Return the borgmatic runtime path as a string.
        '''
        return self.runtime_path

    def __exit__(self, exception_type, exception, traceback):
        '''
        Delete any temporary directory that was created as part of initialization.
        '''
        if self.temporary_directory:
            try:
                self.temporary_directory.cleanup()
            # The cleanup() call errors if, for instance, there's still a
            # mounted filesystem within the temporary directory. There's
            # nothing we can do about that here, so swallow the error.
            except OSError:
                pass


def make_runtime_directory_glob(borgmatic_runtime_directory):
    '''
    Given a borgmatic runtime directory path, make a glob that would match that path, specifically
    replacing any randomly generated temporary subdirectory with "*" since such a directory's name
    changes on every borgmatic run.
    '''
    return os.path.join(
        *(
            '*' if subdirectory.startswith(TEMPORARY_DIRECTORY_PREFIX) else subdirectory
            for subdirectory in os.path.normpath(borgmatic_runtime_directory).split(os.path.sep)
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
            or os.environ.get('XDG_STATE_HOME')
            or os.environ.get('STATE_DIRECTORY')  # Set by systemd if configured.
            or '~/.local/state',
            'borgmatic',
        )
    )
