from flexmock import flexmock
import sys


def builtins_mock():
    try:
        # Python 2
        return flexmock(sys.modules['__builtin__'])
    except KeyError:
        # Python 3
        return flexmock(sys.modules['builtins'])
