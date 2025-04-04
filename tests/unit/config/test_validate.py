import os
import sys
from io import StringIO

import pytest
from flexmock import flexmock

from borgmatic.config import validate as module


def test_schema_filename_finds_schema_path():
    schema_path = '/var/borgmatic/config/schema.yaml'

    flexmock(os.path).should_receive('dirname').and_return('/var/borgmatic/config')
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args(schema_path).and_return(StringIO())
    assert module.schema_filename() == schema_path


def test_schema_filename_raises_filenotfounderror():
    schema_path = '/var/borgmatic/config/schema.yaml'

    flexmock(os.path).should_receive('dirname').and_return('/var/borgmatic/config')
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args(schema_path).and_raise(FileNotFoundError)

    with pytest.raises(FileNotFoundError):
        module.schema_filename()


def test_format_json_error_path_element_formats_array_index():
    module.format_json_error_path_element(3) == '[3]'


def test_format_json_error_path_element_formats_property():
    module.format_json_error_path_element('foo') == '.foo'


def test_format_json_error_formats_error_including_path():
    flexmock(module).format_json_error_path_element = lambda element: f'.{element}'
    error = flexmock(message='oops', path=['foo', 'bar'])

    assert module.format_json_error(error) == "At 'foo.bar': oops"


def test_format_json_error_formats_error_without_path():
    flexmock(module).should_receive('format_json_error_path_element').never()
    error = flexmock(message='oops', path=[])

    assert module.format_json_error(error) == 'At the top level: oops'


def test_validation_error_string_contains_errors():
    flexmock(module).format_json_error = lambda error: error.message
    error = module.Validation_error('config.yaml', ('oops', 'uh oh'))

    result = str(error)

    assert 'config.yaml' in result
    assert 'oops' in result
    assert 'uh oh' in result


def test_apply_logical_validation_raises_if_unknown_repository_in_check_repositories():
    flexmock(module).should_receive('repositories_match').and_return(False)

    with pytest.raises(module.Validation_error):
        module.apply_logical_validation(
            'config.yaml',
            {
                'repositories': ['repo.borg', 'other.borg'],
                'keep_secondly': 1000,
                'check_repositories': ['repo.borg', 'unknown.borg'],
            },
        )


def test_apply_logical_validation_does_not_raise_if_known_repository_in_check_repositories():
    flexmock(module).should_receive('repositories_match').and_return(True)

    module.apply_logical_validation(
        'config.yaml',
        {
            'repositories': [{'path': 'repo.borg'}, {'path': 'other.borg'}],
            'keep_secondly': 1000,
            'check_repositories': ['repo.borg'],
        },
    )


def test_normalize_repository_path_passes_through_remote_repository():
    repository = 'example.org:test.borg'

    module.normalize_repository_path(repository) == repository


def test_normalize_repository_path_passes_through_remote_repository_with_base_dir():
    repository = 'example.org:test.borg'

    flexmock(module.os.path).should_receive('abspath').never()
    module.normalize_repository_path(repository, '/working') == repository


def test_normalize_repository_path_passes_through_file_repository():
    repository = 'file:///foo/bar/test.borg'
    flexmock(module.os.path).should_receive('abspath').with_args('/foo/bar/test.borg').and_return(
        '/foo/bar/test.borg'
    )

    module.normalize_repository_path(repository) == '/foo/bar/test.borg'


def test_normalize_repository_path_passes_through_absolute_file_repository_with_base_dir():
    repository = 'file:///foo/bar/test.borg'
    flexmock(module.os.path).should_receive('abspath').with_args('/foo/bar/test.borg').and_return(
        '/foo/bar/test.borg'
    )

    module.normalize_repository_path(repository, '/working') == '/foo/bar/test.borg'


def test_normalize_repository_path_resolves_relative_file_repository_with_base_dir():
    repository = 'file://foo/bar/test.borg'
    flexmock(module.os.path).should_receive('abspath').with_args(
        '/working/foo/bar/test.borg'
    ).and_return('/working/foo/bar/test.borg')

    module.normalize_repository_path(repository, '/working') == '/working/foo/bar/test.borg'


def test_normalize_repository_path_passes_through_absolute_repository():
    repository = '/foo/bar/test.borg'
    flexmock(module.os.path).should_receive('abspath').and_return(repository)

    module.normalize_repository_path(repository) == repository


def test_normalize_repository_path_passes_through_absolute_repository_with_base_dir():
    repository = '/foo/bar/test.borg'
    flexmock(module.os.path).should_receive('abspath').and_return(repository)

    module.normalize_repository_path(repository, '/working') == repository


def test_normalize_repository_path_resolves_relative_repository():
    repository = 'test.borg'
    absolute = '/foo/bar/test.borg'
    flexmock(module.os.path).should_receive('abspath').with_args(repository).and_return(absolute)

    module.normalize_repository_path(repository) == absolute


def test_normalize_repository_path_resolves_relative_repository_with_base_dir():
    repository = 'test.borg'
    base = '/working'
    absolute = '/working/test.borg'
    flexmock(module.os.path).should_receive('abspath').with_args('/working/test.borg').and_return(
        absolute
    )

    module.normalize_repository_path(repository, base) == absolute


@pytest.mark.parametrize(
    'first,second,expected_result',
    (
        (None, None, False),
        ('foo', None, False),
        (None, 'bar', False),
        ('foo', 'foo', True),
        ('foo', 'bar', False),
        ('foo*', 'foof', True),
        ('barf', 'bar*', True),
        ('foo*', 'bar*', False),
    ),
)
def test_glob_match_matches_globs(first, second, expected_result):
    assert module.glob_match(first=first, second=second) is expected_result


def test_repositories_match_matches_on_path():
    flexmock(module).should_receive('normalize_repository_path')
    flexmock(module).should_receive('glob_match').replace_with(
        lambda first, second: first == second
    )

    module.repositories_match(
        {'path': 'foo', 'label': 'my repo'}, {'path': 'foo', 'label': 'other repo'}
    ) is True


def test_repositories_match_matches_on_label():
    flexmock(module).should_receive('normalize_repository_path')
    flexmock(module).should_receive('glob_match').replace_with(
        lambda first, second: first == second
    )

    module.repositories_match(
        {'path': 'foo', 'label': 'my repo'}, {'path': 'bar', 'label': 'my repo'}
    ) is True


def test_repositories_match_with_different_paths_and_labels_does_not_match():
    flexmock(module).should_receive('normalize_repository_path')
    flexmock(module).should_receive('glob_match').replace_with(
        lambda first, second: first == second
    )

    module.repositories_match(
        {'path': 'foo', 'label': 'my repo'}, {'path': 'bar', 'label': 'other repo'}
    ) is False


def test_repositories_match_matches_on_string_repository():
    flexmock(module).should_receive('normalize_repository_path')
    flexmock(module).should_receive('glob_match').replace_with(
        lambda first, second: first == second
    )

    module.repositories_match('foo', 'foo') is True


def test_repositories_match_with_different_string_repositories_does_not_match():
    flexmock(module).should_receive('normalize_repository_path')
    flexmock(module).should_receive('glob_match').replace_with(
        lambda first, second: first == second
    )

    module.repositories_match('foo', 'bar') is False


def test_repositories_match_supports_mixed_repositories():
    flexmock(module).should_receive('normalize_repository_path')
    flexmock(module).should_receive('glob_match').replace_with(
        lambda first, second: first == second
    )

    module.repositories_match({'path': 'foo', 'label': 'my foo'}, 'bar') is False


def test_guard_configuration_contains_repository_does_not_raise_when_repository_matches():
    flexmock(module).should_receive('repositories_match').and_return(True)

    module.guard_configuration_contains_repository(
        repository='repo',
        configurations={'config.yaml': {'repositories': [{'path': 'foo/bar', 'label': 'repo'}]}},
    )


def test_guard_configuration_contains_repository_does_not_raise_when_repository_is_none():
    flexmock(module).should_receive('repositories_match').never()

    module.guard_configuration_contains_repository(
        repository=None,
        configurations={'config.yaml': {'repositories': [{'path': 'foo/bar', 'label': 'repo'}]}},
    )


def test_guard_configuration_contains_repository_errors_when_repository_does_not_match():
    flexmock(module).should_receive('repositories_match').and_return(False)

    with pytest.raises(ValueError):
        module.guard_configuration_contains_repository(
            repository='nope',
            configurations={'config.yaml': {'repositories': ['repo', 'repo2']}},
        )
