import sys

from nose.tools import assert_raises

from atticmatic import command as module


def test_parse_arguments_with_no_arguments_uses_defaults():
    parser = module.parse_arguments()

    assert parser.config_filename == module.DEFAULT_CONFIG_FILENAME
    assert parser.excludes_filename == module.DEFAULT_EXCLUDES_FILENAME
    assert parser.verbose == False


def test_parse_arguments_with_filename_arguments_overrides_defaults():
    parser = module.parse_arguments('--config', 'myconfig', '--excludes', 'myexcludes')

    assert parser.config_filename == 'myconfig'
    assert parser.excludes_filename == 'myexcludes'
    assert parser.verbose == False


def test_parse_arguments_with_verbose_flag_overrides_default():
    parser = module.parse_arguments('--verbose')

    assert parser.config_filename == module.DEFAULT_CONFIG_FILENAME
    assert parser.excludes_filename == module.DEFAULT_EXCLUDES_FILENAME
    assert parser.verbose == True


def test_parse_arguments_with_invalid_arguments_exits():
    original_stderr = sys.stderr
    sys.stderr = sys.stdout

    try:
        with assert_raises(SystemExit):
            module.parse_arguments('--posix-me-harder')
    finally:
        sys.stderr = original_stderr
