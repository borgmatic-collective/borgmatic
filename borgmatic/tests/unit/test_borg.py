from collections import OrderedDict
from subprocess import STDOUT
import sys
import os

from flexmock import flexmock

from borgmatic import borg as module
from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


def test_initialize_with_passphrase_should_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({'encryption_passphrase': 'pass'}, command='borg')
        assert os.environ.get('BORG_PASSPHRASE') == 'pass'
    finally:
        os.environ = orig_environ


def test_initialize_without_passphrase_should_not_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({}, command='borg')
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
    subprocess = flexmock(STDOUT=STDOUT)
    subprocess.should_receive('check_call').with_args(check_call_command, **kwargs).once()
    flexmock(module).subprocess = subprocess


def insert_subprocess_never():
    subprocess = flexmock()
    subprocess.should_receive('check_call').never()
    flexmock(module).subprocess = subprocess


def insert_platform_mock():
    flexmock(module.platform).should_receive('node').and_return('host')


def insert_datetime_mock():
    flexmock(module).datetime = flexmock().should_receive('now').and_return(
        flexmock().should_receive('isoformat').and_return('now').mock
    ).mock


CREATE_COMMAND = ('borg', 'create', 'repo::host-now', 'foo', 'bar')


def test_create_archive_should_call_borg_with_parameters():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(CREATE_COMMAND)
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        exclude_patterns=None,
        verbosity=None,
        storage_config={},
        source_directories=['foo', 'bar'],
        repository='repo',
        command='borg',
    )


def test_create_archive_with_exclude_patterns_should_call_borg_with_excludes():
    flexmock(module).should_receive('_write_exclude_file').and_return(flexmock(name='excludes'))
    insert_subprocess_mock(CREATE_COMMAND + ('--exclude-from', 'excludes'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        exclude_patterns=['exclude'],
        verbosity=None,
        storage_config={},
        source_directories=['foo', 'bar'],
        repository='repo',
        command='borg',
    )


def test_create_archive_with_verbosity_some_should_call_borg_with_info_parameter():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(CREATE_COMMAND + ('--info', '--stats',))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        exclude_patterns=None,
        verbosity=VERBOSITY_SOME,
        storage_config={},
        source_directories=['foo', 'bar'],
        repository='repo',
        command='borg',
    )


def test_create_archive_with_verbosity_lots_should_call_borg_with_debug_parameter():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(CREATE_COMMAND + ('--debug', '--list', '--stats'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        exclude_patterns=None,
        verbosity=VERBOSITY_LOTS,
        storage_config={},
        source_directories=['foo', 'bar'],
        repository='repo',
        command='borg',
    )


def test_create_archive_with_compression_should_call_borg_with_compression_parameters():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(CREATE_COMMAND + ('--compression', 'rle'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        exclude_patterns=None,
        verbosity=None,
        storage_config={'compression': 'rle'},
        source_directories=['foo', 'bar'],
        repository='repo',
        command='borg',
    )


def test_create_archive_with_one_file_system_should_call_borg_with_one_file_system_parameters():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(CREATE_COMMAND + ('--one-file-system',))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        exclude_patterns=None,
        verbosity=None,
        storage_config={},
        source_directories=['foo', 'bar'],
        repository='repo',
        command='borg',
        one_file_system=True,
    )


def test_create_archive_with_remote_path_should_call_borg_with_remote_path_parameters():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(CREATE_COMMAND + ('--remote-path', 'borg1'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        exclude_patterns=None,
        verbosity=None,
        storage_config={},
        source_directories=['foo', 'bar'],
        repository='repo',
        command='borg',
        remote_path='borg1',
    )


def test_create_archive_with_umask_should_call_borg_with_umask_parameters():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(CREATE_COMMAND + ('--umask', '740'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        exclude_patterns=None,
        verbosity=None,
        storage_config={'umask': 740},
        source_directories=['foo', 'bar'],
        repository='repo',
        command='borg',
    )


def test_create_archive_with_source_directories_glob_expands():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(('borg', 'create', 'repo::host-now', 'foo', 'food'))
    insert_platform_mock()
    insert_datetime_mock()
    flexmock(module.glob).should_receive('glob').with_args('foo*').and_return(['foo', 'food'])

    module.create_archive(
        exclude_patterns=None,
        verbosity=None,
        storage_config={},
        source_directories=['foo*'],
        repository='repo',
        command='borg',
    )


def test_create_archive_with_non_matching_source_directories_glob_passes_through():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(('borg', 'create', 'repo::host-now', 'foo*'))
    insert_platform_mock()
    insert_datetime_mock()
    flexmock(module.glob).should_receive('glob').with_args('foo*').and_return([])

    module.create_archive(
        exclude_patterns=None,
        verbosity=None,
        storage_config={},
        source_directories=['foo*'],
        repository='repo',
        command='borg',
    )


def test_create_archive_with_glob_should_call_borg_with_expanded_directories():
    flexmock(module).should_receive('_write_exclude_file')
    insert_subprocess_mock(('borg', 'create', 'repo::host-now', 'foo', 'food'))
    insert_platform_mock()
    insert_datetime_mock()
    flexmock(module.glob).should_receive('glob').with_args('foo*').and_return(['foo', 'food'])

    module.create_archive(
        exclude_patterns=None,
        verbosity=None,
        storage_config={},
        source_directories=['foo*'],
        repository='repo',
        command='borg',
    )


BASE_PRUNE_FLAGS = (
    ('--keep-daily', '1'),
    ('--keep-weekly', '2'),
    ('--keep-monthly', '3'),
)


def test_make_prune_flags_should_return_flags_from_config():
    retention_config = OrderedDict(
        (
            ('keep_daily', 1),
            ('keep_weekly', 2),
            ('keep_monthly', 3),
        )
    )

    result = module._make_prune_flags(retention_config)

    assert tuple(result) == BASE_PRUNE_FLAGS


PRUNE_COMMAND = (
    'borg', 'prune', 'repo', '--keep-daily', '1', '--keep-weekly', '2', '--keep-monthly', '3',
)


def test_prune_archives_should_call_borg_with_parameters():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(PRUNE_COMMAND)

    module.prune_archives(
        verbosity=None,
        repository='repo',
        retention_config=retention_config,
        command='borg',
    )


def test_prune_archives_with_verbosity_some_should_call_borg_with_info_parameter():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(PRUNE_COMMAND + ('--info', '--stats',))

    module.prune_archives(
        repository='repo',
        verbosity=VERBOSITY_SOME,
        retention_config=retention_config,
        command='borg',
    )


def test_prune_archives_with_verbosity_lots_should_call_borg_with_debug_parameter():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(PRUNE_COMMAND + ('--debug', '--stats',))

    module.prune_archives(
        repository='repo',
        verbosity=VERBOSITY_LOTS,
        retention_config=retention_config,
        command='borg',
    )

def test_prune_archive_with_remote_path_should_call_borg_with_remote_path_parameters():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(PRUNE_COMMAND + ('--remote-path', 'borg1'))

    module.prune_archives(
        verbosity=None,
        repository='repo',
        retention_config=retention_config,
        command='borg',
        remote_path='borg1',
    )


def test_parse_checks_returns_them_as_tuple():
    checks = module._parse_checks({'checks': ['foo', 'disabled', 'bar']})

    assert checks == ('foo', 'bar')


def test_parse_checks_with_missing_value_returns_defaults():
    checks = module._parse_checks({})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_blank_value_returns_defaults():
    checks = module._parse_checks({'checks': []})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_disabled_returns_no_checks():
    checks = module._parse_checks({'checks': ['disabled']})

    assert checks == ()


def test_make_check_flags_with_checks_returns_flags():
    flags = module._make_check_flags(('foo', 'bar'))

    assert flags == ('--foo-only', '--bar-only')


def test_make_check_flags_with_default_checks_returns_no_flags():
    flags = module._make_check_flags(module.DEFAULT_CHECKS)

    assert flags == ()


def test_make_check_flags_with_checks_and_last_returns_flags_including_last():
    flags = module._make_check_flags(('foo', 'bar'), check_last=3)

    assert flags == ('--foo-only', '--bar-only', '--last', 3)


def test_make_check_flags_with_last_returns_last_flag():
    flags = module._make_check_flags(module.DEFAULT_CHECKS, check_last=3)

    assert flags == ('--last', 3)


def test_check_archives_should_call_borg_with_parameters():
    checks = flexmock()
    check_last = flexmock()
    consistency_config = flexmock().should_receive('get').and_return(check_last).mock
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(checks, check_last).and_return(())
    stdout = flexmock()
    insert_subprocess_mock(
        ('borg', 'check', 'repo'),
        stdout=stdout, stderr=STDOUT,
    )
    insert_platform_mock()
    insert_datetime_mock()
    flexmock(sys.modules['builtins']).should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

    module.check_archives(
        verbosity=None,
        repository='repo',
        consistency_config=consistency_config,
        command='borg',
    )


def test_check_archives_with_verbosity_some_should_call_borg_with_info_parameter():
    consistency_config = flexmock().should_receive('get').and_return(None).mock
    flexmock(module).should_receive('_parse_checks').and_return(flexmock())
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_subprocess_mock(
        ('borg', 'check', 'repo', '--info'),
        stdout=None, stderr=STDOUT,
    )
    insert_platform_mock()
    insert_datetime_mock()

    module.check_archives(
        verbosity=VERBOSITY_SOME,
        repository='repo',
        consistency_config=consistency_config,
        command='borg',
    )


def test_check_archives_with_verbosity_lots_should_call_borg_with_debug_parameter():
    consistency_config = flexmock().should_receive('get').and_return(None).mock
    flexmock(module).should_receive('_parse_checks').and_return(flexmock())
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_subprocess_mock(
        ('borg', 'check', 'repo', '--debug'),
        stdout=None, stderr=STDOUT,
    )
    insert_platform_mock()
    insert_datetime_mock()

    module.check_archives(
        verbosity=VERBOSITY_LOTS,
        repository='repo',
        consistency_config=consistency_config,
        command='borg',
    )


def test_check_archives_without_any_checks_should_bail():
    consistency_config = flexmock().should_receive('get').and_return(None).mock
    flexmock(module).should_receive('_parse_checks').and_return(())
    insert_subprocess_never()

    module.check_archives(
        verbosity=None,
        repository='repo',
        consistency_config=consistency_config,
        command='borg',
    )


def test_check_archives_with_remote_path_should_call_borg_with_remote_path_parameters():
    checks = flexmock()
    check_last = flexmock()
    consistency_config = flexmock().should_receive('get').and_return(check_last).mock
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(checks, check_last).and_return(())
    stdout = flexmock()
    insert_subprocess_mock(
        ('borg', 'check', 'repo', '--remote-path', 'borg1'),
        stdout=stdout, stderr=STDOUT,
    )
    insert_platform_mock()
    insert_datetime_mock()
    flexmock(sys.modules['builtins']).should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

    module.check_archives(
        verbosity=None,
        repository='repo',
        consistency_config=consistency_config,
        command='borg',
        remote_path='borg1',
    )
