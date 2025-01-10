import collections
import enum


# See https://borgbackup.readthedocs.io/en/stable/usage/help.html#borg-help-patterns
class Pattern_type(enum.Enum):
    ROOT = 'R'  # A ROOT pattern type always has a NONE pattern style.
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


Pattern = collections.namedtuple(
    'Pattern',
    ('path', 'type', 'style', 'device'),
    defaults=(
        Pattern_type.ROOT,
        Pattern_style.NONE,
        None,
    ),
)
