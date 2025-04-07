import pytest
from flexmock import flexmock

from borgmatic.borg import pattern as module
from borgmatic.borg.pattern import Pattern, Pattern_style, Pattern_type


def test_write_patterns_file_writes_pattern_lines():
    temporary_file = flexmock(name='filename', flush=lambda: None)
    temporary_file.should_receive('write').with_args('R /foo\n+ sh:/foo/bar')
    flexmock(module.tempfile).should_receive('NamedTemporaryFile').and_return(temporary_file)

    module.write_patterns_file(
        [Pattern('/foo'), Pattern('/foo/bar', Pattern_type.INCLUDE, Pattern_style.SHELL)],
        borgmatic_runtime_directory='/run/user/0',
    )


def test_write_patterns_file_with_empty_exclude_patterns_does_not_raise():
    module.write_patterns_file([], borgmatic_runtime_directory='/run/user/0')


def test_write_patterns_file_appends_to_existing():
    patterns_file = flexmock(name='filename', flush=lambda: None)
    patterns_file.should_receive('write').with_args('\n')
    patterns_file.should_receive('write').with_args('R /foo\n+ /foo/bar')
    flexmock(module.tempfile).should_receive('NamedTemporaryFile').never()

    module.write_patterns_file(
        [Pattern('/foo'), Pattern('/foo/bar', Pattern_type.INCLUDE)],
        borgmatic_runtime_directory='/run/user/0',
        patterns_file=patterns_file,
    )


def test_check_all_root_patterns_exist_with_existent_pattern_path_does_not_raise():
    flexmock(module.os.path).should_receive('exists').and_return(True)

    module.check_all_root_patterns_exist([Pattern('foo')])


def test_check_all_root_patterns_exist_with_non_root_pattern_skips_existence_check():
    flexmock(module.os.path).should_receive('exists').never()

    module.check_all_root_patterns_exist([Pattern('foo', Pattern_type.INCLUDE)])


def test_check_all_root_patterns_exist_with_non_existent_pattern_path_raises():
    flexmock(module.os.path).should_receive('exists').and_return(False)

    with pytest.raises(ValueError):
        module.check_all_root_patterns_exist([Pattern('foo')])
