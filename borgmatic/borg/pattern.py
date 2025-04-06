import collections
import enum
import logging
import os
import tempfile

import borgmatic.borg.pattern

logger = logging.getLogger(__name__)


# See https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-help-patterns
class Pattern_type(enum.Enum):
    ROOT = 'R'  # A ROOT pattern always has a NONE pattern style.
    PATTERN_STYLE = 'P'
    EXCLUDE = '-'
    NO_RECURSE = '!'
    INCLUDE = '+'


class Pattern_style(enum.Enum):
    NONE = ''
    FNMATCH = 'fm'
    SHELL = 'sh'
    REGULAR_EXPRESSION = 're'
    PATH_PREFIX = 'pp'
    PATH_FULL_MATCH = 'pf'


class Pattern_source(enum.Enum):
    '''
    Where the pattern came from within borgmatic. This is important because certain use cases (like
    filesystem snapshotting) only want to consider patterns that the user actually put in a
    configuration file and not patterns from other sources.
    '''

    # The pattern is from a borgmatic configuration option, e.g. listed in "source_directories".
    CONFIG = 'config'

    # The pattern is generated internally within borgmatic, e.g. for special file excludes.
    INTERNAL = 'internal'

    # The pattern originates from within a borgmatic hook, e.g. a database hook that adds its dump
    # directory.
    HOOK = 'hook'


Pattern = collections.namedtuple(
    'Pattern',
    ('path', 'type', 'style', 'device', 'source'),
    defaults=(
        Pattern_type.ROOT,
        Pattern_style.NONE,
        None,
        Pattern_source.HOOK,
    ),
)


def write_patterns_file(patterns, borgmatic_runtime_directory, patterns_file=None):
    '''
    Given a sequence of patterns as borgmatic.borg.pattern.Pattern instances, write them to a named
    temporary file in the given borgmatic runtime directory and return the file object so it can
    continue to exist on disk as long as the caller needs it.

    If an optional open pattern file is given, append to it instead of making a new temporary file.
    Return None if no patterns are provided.
    '''
    if not patterns:
        return None

    if patterns_file is None:
        patterns_file = tempfile.NamedTemporaryFile('w', dir=borgmatic_runtime_directory)
        operation_name = 'Writing'
    else:
        patterns_file.write('\n')
        operation_name = 'Appending'

    patterns_output = '\n'.join(
        f'{pattern.type.value} {pattern.style.value}{":" if pattern.style.value else ""}{pattern.path}'
        for pattern in patterns
    )
    logger.debug(f'{operation_name} patterns to {patterns_file.name}:\n{patterns_output}')

    patterns_file.write(patterns_output)
    patterns_file.flush()

    return patterns_file


def check_all_root_patterns_exist(patterns):
    '''
    Given a sequence of borgmatic.borg.pattern.Pattern instances, check that all root pattern
    paths exist. If any don't, raise an exception.
    '''
    missing_paths = [
        pattern.path
        for pattern in patterns
        if pattern.type == borgmatic.borg.pattern.Pattern_type.ROOT
        if not os.path.exists(pattern.path)
    ]

    if missing_paths:
        raise ValueError(
            f"Source directories or root pattern paths do not exist: {', '.join(missing_paths)}"
        )
