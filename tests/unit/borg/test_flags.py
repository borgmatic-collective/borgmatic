import pytest
from flexmock import flexmock

from borgmatic.borg import flags as module


def test_make_flags_formats_string_value():
    assert module.make_flags('foo', 'bar') == ('--foo', 'bar')


def test_make_flags_formats_integer_value():
    assert module.make_flags('foo', 3) == ('--foo', '3')


def test_make_flags_formats_true_value():
    assert module.make_flags('foo', True) == ('--foo',)


def test_make_flags_omits_false_value():
    assert module.make_flags('foo', False) == ()


def test_make_flags_formats_name_with_underscore():
    assert module.make_flags('posix_me_harder', 'okay') == ('--posix-me-harder', 'okay')


def test_make_flags_from_arguments_flattens_and_sorts_multiple_arguments():
    flexmock(module).should_receive('make_flags').with_args('foo', 'bar').and_return(('foo', 'bar'))
    flexmock(module).should_receive('make_flags').with_args('baz', 'quux').and_return(
        ('baz', 'quux')
    )
    arguments = flexmock(foo='bar', baz='quux')

    assert module.make_flags_from_arguments(arguments) == ('baz', 'quux', 'foo', 'bar')


def test_make_flags_from_arguments_excludes_underscored_argument_names():
    flexmock(module).should_receive('make_flags').with_args('foo', 'bar').and_return(('foo', 'bar'))
    arguments = flexmock(foo='bar', _baz='quux')

    assert module.make_flags_from_arguments(arguments) == ('foo', 'bar')


def test_make_flags_from_arguments_omits_excludes():
    flexmock(module).should_receive('make_flags').with_args('foo', 'bar').and_return(('foo', 'bar'))
    arguments = flexmock(foo='bar', baz='quux')

    assert module.make_flags_from_arguments(arguments, excludes=('baz', 'other')) == ('foo', 'bar')


def test_make_repository_flags_with_borg_features_includes_repo_flag():
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_repository_flags(repository_path='repo', local_borg_version='1.2.3') == (
        '--repo',
        'repo',
    )


def test_make_repository_flags_without_borg_features_includes_omits_flag():
    flexmock(module.feature).should_receive('available').and_return(False)

    assert module.make_repository_flags(repository_path='repo', local_borg_version='1.2.3') == (
        'repo',
    )


def test_make_repository_archive_flags_with_borg_features_separates_repository_and_archive():
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_repository_archive_flags(
        repository_path='repo', archive='archive', local_borg_version='1.2.3'
    ) == (
        '--repo',
        'repo',
        'archive',
    )


def test_make_repository_archive_flags_with_borg_features_joins_repository_and_archive():
    flexmock(module.feature).should_receive('available').and_return(False)

    assert module.make_repository_archive_flags(
        repository_path='repo', archive='archive', local_borg_version='1.2.3'
    ) == ('repo::archive',)


@pytest.mark.parametrize(
    'match_archives,archive_name_format,feature_available,expected_result',
    (
        (None, None, True, ()),
        (None, '', True, ()),
        (
            're:foo-.*',
            '{hostname}-{now}',  # noqa: FS003
            True,
            ('--match-archives', 're:foo-.*'),
        ),
        (
            'sh:foo-*',
            '{hostname}-{now}',  # noqa: FS003
            False,
            ('--glob-archives', 'foo-*'),
        ),
        (
            'foo-*',
            '{hostname}-{now}',  # noqa: FS003
            False,
            ('--glob-archives', 'foo-*'),
        ),
        (
            None,
            '{hostname}-docs-{now}',  # noqa: FS003
            True,
            ('--match-archives', 'sh:{hostname}-docs-*'),  # noqa: FS003
        ),
        (
            None,
            '{utcnow}-docs-{user}',  # noqa: FS003
            True,
            ('--match-archives', 'sh:*-docs-{user}'),  # noqa: FS003
        ),
        (None, '{fqdn}-{pid}', True, ('--match-archives', 'sh:{fqdn}-*')),  # noqa: FS003
        (
            None,
            'stuff-{now:%Y-%m-%dT%H:%M:%S.%f}',  # noqa: FS003
            True,
            ('--match-archives', 'sh:stuff-*'),
        ),
        (
            None,
            '{hostname}-docs-{now}',  # noqa: FS003
            False,
            ('--glob-archives', '{hostname}-docs-*'),  # noqa: FS003
        ),
        (
            None,
            '{now}',  # noqa: FS003
            False,
            (),
        ),
        (
            None,
            '{now}',  # noqa: FS003
            True,
            (),
        ),
        (None, '{utcnow}-docs-{user}', False, ('--glob-archives', '*-docs-{user}')),  # noqa: FS003
    ),
)
def test_make_match_archives_flags_makes_flags_with_globs(
    match_archives, archive_name_format, feature_available, expected_result
):
    flexmock(module.feature).should_receive('available').and_return(feature_available)

    assert (
        module.make_match_archives_flags(
            match_archives, archive_name_format, local_borg_version=flexmock()
        )
        == expected_result
    )
