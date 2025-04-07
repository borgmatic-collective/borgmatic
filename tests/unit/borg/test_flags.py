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


def test_get_default_archive_name_format_with_archive_series_feature_uses_series_archive_name_format():
    flexmock(module.feature).should_receive('available').and_return(True)

    assert (
        module.get_default_archive_name_format(local_borg_version='1.2.3')
        == module.DEFAULT_ARCHIVE_NAME_FORMAT_WITH_SERIES
    )


def test_get_default_archive_name_format_without_archive_series_feature_uses_non_series_archive_name_format():
    flexmock(module.feature).should_receive('available').and_return(False)

    assert (
        module.get_default_archive_name_format(local_borg_version='1.2.3')
        == module.DEFAULT_ARCHIVE_NAME_FORMAT_WITHOUT_SERIES
    )


@pytest.mark.parametrize(
    'match_archives,archive_name_format,feature_available,expected_result',
    (
        (None, None, True, ('--match-archives', 'sh:{hostname}-*')),  # noqa: FS003
        (None, '', True, ('--match-archives', 'sh:{hostname}-*')),  # noqa: FS003
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
        (
            None,
            '{utcnow}-docs-{user}',  # noqa: FS003
            False,
            ('--glob-archives', '*-docs-{user}'),  # noqa: FS003
        ),
        (
            '*',
            '{now}',  # noqa: FS003
            True,
            (),
        ),
        (
            '*',
            '{now}',  # noqa: FS003
            False,
            (),
        ),
        (
            're:.*',
            '{now}',  # noqa: FS003
            True,
            (),
        ),
        (
            'sh:*',
            '{now}',  # noqa: FS003
            True,
            (),
        ),
        (
            'abcdefabcdef',
            None,
            True,
            ('--match-archives', 'aid:abcdefabcdef'),
        ),
        (
            'aid:abcdefabcdef',
            None,
            True,
            ('--match-archives', 'aid:abcdefabcdef'),
        ),
    ),
)
def test_make_match_archives_flags_makes_flags_with_globs(
    match_archives, archive_name_format, feature_available, expected_result
):
    flexmock(module.feature).should_receive('available').and_return(feature_available)
    flexmock(module).should_receive('get_default_archive_name_format').and_return(
        module.DEFAULT_ARCHIVE_NAME_FORMAT_WITHOUT_SERIES
    )

    assert (
        module.make_match_archives_flags(
            match_archives, archive_name_format, local_borg_version=flexmock()
        )
        == expected_result
    )


def test_make_match_archives_flags_accepts_default_archive_name_format():
    flexmock(module.feature).should_receive('available').and_return(True)

    assert (
        module.make_match_archives_flags(
            match_archives=None,
            archive_name_format=None,
            local_borg_version=flexmock(),
            default_archive_name_format='*',
        )
        == ()
    )


def test_warn_for_aggressive_archive_flags_without_archive_flags_bails():
    flexmock(module.logger).should_receive('warning').never()

    module.warn_for_aggressive_archive_flags(('borg', '--do-stuff'), '{}')


def test_warn_for_aggressive_archive_flags_with_glob_archives_and_zero_archives_warns():
    flexmock(module.logger).should_receive('warning').twice()

    module.warn_for_aggressive_archive_flags(
        ('borg', '--glob-archives', 'foo*'), '{"archives": []}'
    )


def test_warn_for_aggressive_archive_flags_with_match_archives_and_zero_archives_warns():
    flexmock(module.logger).should_receive('warning').twice()

    module.warn_for_aggressive_archive_flags(
        ('borg', '--match-archives', 'foo*'), '{"archives": []}'
    )


def test_warn_for_aggressive_archive_flags_with_glob_archives_and_one_archive_does_not_warn():
    flexmock(module.logger).should_receive('warning').never()

    module.warn_for_aggressive_archive_flags(
        ('borg', '--glob-archives', 'foo*'), '{"archives": [{"name": "foo"]}'
    )


def test_warn_for_aggressive_archive_flags_with_match_archives_and_one_archive_does_not_warn():
    flexmock(module.logger).should_receive('warning').never()

    module.warn_for_aggressive_archive_flags(
        ('borg', '--match-archives', 'foo*'), '{"archives": [{"name": "foo"]}'
    )


def test_warn_for_aggressive_archive_flags_with_glob_archives_and_invalid_json_does_not_warn():
    flexmock(module.logger).should_receive('warning').never()

    module.warn_for_aggressive_archive_flags(('borg', '--glob-archives', 'foo*'), '{"archives": [}')


def test_warn_for_aggressive_archive_flags_with_glob_archives_and_json_missing_archives_does_not_warn():
    flexmock(module.logger).should_receive('warning').never()

    module.warn_for_aggressive_archive_flags(('borg', '--glob-archives', 'foo*'), '{}')


def test_omit_flag_removes_flag_from_arguments():
    assert module.omit_flag(('borg', 'create', '--flag', '--other'), '--flag') == (
        'borg',
        'create',
        '--other',
    )


def test_omit_flag_without_flag_present_passes_through_arguments():
    assert module.omit_flag(('borg', 'create', '--other'), '--flag') == (
        'borg',
        'create',
        '--other',
    )


def test_omit_flag_and_value_removes_flag_and_value_from_arguments():
    assert module.omit_flag_and_value(
        ('borg', 'create', '--flag', 'value', '--other'), '--flag'
    ) == (
        'borg',
        'create',
        '--other',
    )


def test_omit_flag_and_value_with_equals_sign_removes_flag_and_value_from_arguments():
    assert module.omit_flag_and_value(('borg', 'create', '--flag=value', '--other'), '--flag') == (
        'borg',
        'create',
        '--other',
    )


def test_omit_flag_and_value_without_flag_present_passes_through_arguments():
    assert module.omit_flag_and_value(('borg', 'create', '--other'), '--flag') == (
        'borg',
        'create',
        '--other',
    )


def test_make_exclude_flags_includes_exclude_caches_when_true_in_config():
    exclude_flags = module.make_exclude_flags(config={'exclude_caches': True})

    assert exclude_flags == ('--exclude-caches',)


def test_make_exclude_flags_does_not_include_exclude_caches_when_false_in_config():
    exclude_flags = module.make_exclude_flags(config={'exclude_caches': False})

    assert exclude_flags == ()


def test_make_exclude_flags_includes_exclude_if_present_when_in_config():
    exclude_flags = module.make_exclude_flags(
        config={'exclude_if_present': ['exclude_me', 'also_me']}
    )

    assert exclude_flags == (
        '--exclude-if-present',
        'exclude_me',
        '--exclude-if-present',
        'also_me',
    )


def test_make_exclude_flags_includes_keep_exclude_tags_when_true_in_config():
    exclude_flags = module.make_exclude_flags(config={'keep_exclude_tags': True})

    assert exclude_flags == ('--keep-exclude-tags',)


def test_make_exclude_flags_does_not_include_keep_exclude_tags_when_false_in_config():
    exclude_flags = module.make_exclude_flags(config={'keep_exclude_tags': False})

    assert exclude_flags == ()


def test_make_exclude_flags_includes_exclude_nodump_when_true_in_config():
    exclude_flags = module.make_exclude_flags(config={'exclude_nodump': True})

    assert exclude_flags == ('--exclude-nodump',)


def test_make_exclude_flags_does_not_include_exclude_nodump_when_false_in_config():
    exclude_flags = module.make_exclude_flags(config={'exclude_nodump': False})

    assert exclude_flags == ()


def test_make_exclude_flags_is_empty_when_config_has_no_excludes():
    exclude_flags = module.make_exclude_flags(config={})

    assert exclude_flags == ()


def test_make_list_filter_flags_with_debug_and_feature_available_includes_plus_and_minus():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(True)
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=False) == 'AME+-'


def test_make_list_filter_flags_with_info_and_feature_available_omits_plus_and_minus():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(False)
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=False) == 'AME'


def test_make_list_filter_flags_with_debug_and_feature_available_and_dry_run_includes_plus_and_minus():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(True)
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=True) == 'AME+-'


def test_make_list_filter_flags_with_info_and_feature_available_and_dry_run_includes_plus_and_minus():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(False)
    flexmock(module.feature).should_receive('available').and_return(True)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=True) == 'AME+-'


def test_make_list_filter_flags_with_debug_and_feature_not_available_includes_x():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(True)
    flexmock(module.feature).should_receive('available').and_return(False)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=False) == 'AMEx-'


def test_make_list_filter_flags_with_info_and_feature_not_available_omits_x():
    flexmock(module.logger).should_receive('isEnabledFor').and_return(False)
    flexmock(module.feature).should_receive('available').and_return(False)

    assert module.make_list_filter_flags(local_borg_version=flexmock(), dry_run=False) == 'AME-'
