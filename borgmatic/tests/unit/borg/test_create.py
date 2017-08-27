import os

from flexmock import flexmock

from borgmatic.borg import create as module
from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


def test_initialize_with_passphrase_should_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({'encryption_passphrase': 'pass'})
        assert os.environ.get('BORG_PASSPHRASE') == 'pass'
    finally:
        os.environ = orig_environ


def test_initialize_without_passphrase_should_not_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({})
        assert os.environ.get('BORG_PASSPHRASE') == None
    finally:
        os.environ = orig_environ


def test_write_exclude_file_does_not_raise():
    temporary_file = flexmock(
        name='filename',
        write=lambda mode: None,
        flush=lambda: None,
    )
    flexmock(module.tempfile).should_receive('NamedTemporaryFile').and_return(temporary_file)

    module._write_exclude_file(['exclude'])


def test_write_exclude_file_with_empty_exclude_patterns_does_not_raise():
    module._write_exclude_file([])


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(check_call_command, **kwargs).once()


def insert_platform_mock():
    flexmock(module.platform).should_receive('node').and_return('host')


def insert_datetime_mock():
    flexmock(module).datetime = flexmock().should_receive('now').and_return(
        flexmock().should_receive('isoformat').and_return('now').mock
    ).mock


def test_make_exclude_flags_includes_exclude_patterns_filename_when_given():
    exclude_flags = module._make_exclude_flags(
        location_config={'exclude_patterns': ['*.pyc', '/var']},
        exclude_patterns_filename='/tmp/excludes',
    )

    assert exclude_flags == ('--exclude-from', '/tmp/excludes')


def test_make_exclude_flags_includes_exclude_from_filenames_when_in_config():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)

    exclude_flags = module._make_exclude_flags(
        location_config={'exclude_from': ['excludes', 'other']},
    )

    assert exclude_flags == ('--exclude-from', 'excludes', '--exclude-from', 'other')


def test_make_exclude_flags_includes_both_filenames_when_patterns_given_and_exclude_from_in_config():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)

    exclude_flags = module._make_exclude_flags(
        location_config={'exclude_from': ['excludes']},
        exclude_patterns_filename='/tmp/excludes',
    )

    assert exclude_flags == ('--exclude-from', 'excludes', '--exclude-from', '/tmp/excludes')


def test_make_exclude_flags_considers_none_exclude_from_filenames_as_empty():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)

    exclude_flags = module._make_exclude_flags(
        location_config={'exclude_from': None},
    )

    assert exclude_flags == ()


def test_make_exclude_flags_includes_exclude_caches_when_true_in_config():
    exclude_flags = module._make_exclude_flags(
        location_config={'exclude_caches': True},
    )

    assert exclude_flags == ('--exclude-caches',)


def test_make_exclude_flags_does_not_include_exclude_caches_when_false_in_config():
    exclude_flags = module._make_exclude_flags(
        location_config={'exclude_caches': False},
    )

    assert exclude_flags == ()


def test_make_exclude_flags_includes_exclude_if_present_when_in_config():
    exclude_flags = module._make_exclude_flags(
        location_config={'exclude_if_present': 'exclude_me'},
    )

    assert exclude_flags == ('--exclude-if-present', 'exclude_me')


def test_make_exclude_flags_is_empty_when_config_has_no_excludes():
    exclude_flags = module._make_exclude_flags(location_config={})

    assert exclude_flags == ()


CREATE_COMMAND = ('borg', 'create', 'repo::host-now', 'foo', 'bar')


def test_create_archive_should_call_borg_with_parameters():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(CREATE_COMMAND)
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        verbosity=None,
        repository='repo',
        location_config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        storage_config={},
    )


def test_create_archive_with_exclude_patterns_should_call_borg_with_excludes():
    exclude_flags = ('--exclude-from', 'excludes')
    flexmock(module).should_receive('_write_exclude_file').and_return(flexmock(name='/tmp/excludes'))
    flexmock(module).should_receive('_make_exclude_flags').and_return(exclude_flags)
    insert_subprocess_mock(CREATE_COMMAND + exclude_flags)
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        verbosity=None,
        repository='repo',
        location_config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': ['exclude'],
        },
        storage_config={},
    )


def test_create_archive_with_verbosity_some_should_call_borg_with_info_parameter():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(CREATE_COMMAND + ('--info', '--stats',))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        verbosity=VERBOSITY_SOME,
        repository='repo',
        location_config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        storage_config={},
    )


def test_create_archive_with_verbosity_lots_should_call_borg_with_debug_parameter():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(CREATE_COMMAND + ('--debug', '--list', '--stats'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        verbosity=VERBOSITY_LOTS,
        repository='repo',
        location_config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        storage_config={},
    )


def test_create_archive_with_compression_should_call_borg_with_compression_parameters():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(CREATE_COMMAND + ('--compression', 'rle'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        verbosity=None,
        repository='repo',
        location_config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        storage_config={'compression': 'rle'},
    )


def test_create_archive_with_one_file_system_should_call_borg_with_one_file_system_parameters():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(CREATE_COMMAND + ('--one-file-system',))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        verbosity=None,
        repository='repo',
        location_config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'one_file_system': True,
            'exclude_patterns': None,
        },
        storage_config={},
    )


def test_create_archive_with_remote_path_should_call_borg_with_remote_path_parameters():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(CREATE_COMMAND + ('--remote-path', 'borg1'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        verbosity=None,
        repository='repo',
        location_config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'remote_path': 'borg1',
            'exclude_patterns': None,
        },
        storage_config={},
    )


def test_create_archive_with_umask_should_call_borg_with_umask_parameters():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(CREATE_COMMAND + ('--umask', '740'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        verbosity=None,
        repository='repo',
        location_config={
            'source_directories': ['foo', 'bar'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        storage_config={'umask': 740},
    )


def test_create_archive_with_source_directories_glob_expands():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(('borg', 'create', 'repo::host-now', 'foo', 'food'))
    insert_platform_mock()
    insert_datetime_mock()
    flexmock(module.glob).should_receive('glob').with_args('foo*').and_return(['foo', 'food'])

    module.create_archive(
        verbosity=None,
        repository='repo',
        location_config={
            'source_directories': ['foo*'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        storage_config={},
    )


def test_create_archive_with_non_matching_source_directories_glob_passes_through():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(('borg', 'create', 'repo::host-now', 'foo*'))
    insert_platform_mock()
    insert_datetime_mock()
    flexmock(module.glob).should_receive('glob').with_args('foo*').and_return([])

    module.create_archive(
        verbosity=None,
        repository='repo',
        location_config={
            'source_directories': ['foo*'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        storage_config={},
    )


def test_create_archive_with_glob_should_call_borg_with_expanded_directories():
    flexmock(module).should_receive('_write_exclude_file').and_return(None)
    flexmock(module).should_receive('_make_exclude_flags').and_return(())
    insert_subprocess_mock(('borg', 'create', 'repo::host-now', 'foo', 'food'))
    insert_platform_mock()
    insert_datetime_mock()
    flexmock(module.glob).should_receive('glob').with_args('foo*').and_return(['foo', 'food'])

    module.create_archive(
        verbosity=None,
        repository='repo',
        location_config={
            'source_directories': ['foo*'],
            'repositories': ['repo'],
            'exclude_patterns': None,
        },
        storage_config={},
    )
