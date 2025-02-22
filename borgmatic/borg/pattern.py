import collections
import enum


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
