from flexmock import flexmock
import sys


def builtins_mock():
    return flexmock(sys.modules['builtins'])
