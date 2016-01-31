from collections import OrderedDict
import os

from flexmock import flexmock

from atticmatic.backends import shared as module
from atticmatic.tests.builtins import builtins_mock
from atticmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


def test_initialize_with_passphrase_should_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({'encryption_passphrase': 'pass'}, command='attic')
        assert os.environ.get('ATTIC_PASSPHRASE') == 'pass'
    finally:
        os.environ = orig_environ


def test_initialize_without_passphrase_should_not_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({}, command='attic')
        assert os.environ.get('ATTIC_PASSPHRASE') == None
    finally:
        os.environ = orig_environ


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock()
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


CREATE_COMMAND_WITHOUT_EXCLUDES = ('attic', 'create', 'repo::host-now', 'foo', 'bar')
CREATE_COMMAND = CREATE_COMMAND_WITHOUT_EXCLUDES + ('--exclude-from', 'excludes')


def test_create_archive_should_call_attic_with_parameters():
    insert_subprocess_mock(CREATE_COMMAND)
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        excludes_filename='excludes',
        verbosity=None,
        storage_config={},
        source_directories='foo bar',
        repository='repo',
        command='attic',
    )


def test_create_archive_with_two_spaces_in_source_directories():
    insert_subprocess_mock(CREATE_COMMAND)
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        excludes_filename='excludes',
        verbosity=None,
        storage_config={},
        source_directories='foo  bar',
        repository='repo',
        command='attic',
    )


def test_create_archive_with_none_excludes_filename_should_call_attic_without_excludes():
    insert_subprocess_mock(CREATE_COMMAND_WITHOUT_EXCLUDES)
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        excludes_filename=None,
        verbosity=None,
        storage_config={},
        source_directories='foo bar',
        repository='repo',
        command='attic',
    )


def test_create_archive_with_verbosity_some_should_call_attic_with_stats_parameter():
    insert_subprocess_mock(CREATE_COMMAND + ('--stats',))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        excludes_filename='excludes',
        verbosity=VERBOSITY_SOME,
        storage_config={},
        source_directories='foo bar',
        repository='repo',
        command='attic',
    )


def test_create_archive_with_verbosity_lots_should_call_attic_with_verbose_parameter():
    insert_subprocess_mock(CREATE_COMMAND + ('--verbose', '--stats'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        excludes_filename='excludes',
        verbosity=VERBOSITY_LOTS,
        storage_config={},
        source_directories='foo bar',
        repository='repo',
        command='attic',
    )


def test_create_archive_with_compression_should_call_attic_with_compression_parameters():
    insert_subprocess_mock(CREATE_COMMAND + ('--compression', 'rle'))
    insert_platform_mock()
    insert_datetime_mock()

    module.create_archive(
        excludes_filename='excludes',
        verbosity=None,
        storage_config={'compression': 'rle'},
        source_directories='foo bar',
        repository='repo',
        command='attic',
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
    'attic', 'prune', 'repo', '--keep-daily', '1', '--keep-weekly', '2', '--keep-monthly', '3',
)


def test_prune_archives_should_call_attic_with_parameters():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(PRUNE_COMMAND)

    module.prune_archives(
        verbosity=None,
        repository='repo',
        retention_config=retention_config,
        command='attic',
    )


def test_prune_archives_with_verbosity_some_should_call_attic_with_stats_parameter():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(PRUNE_COMMAND + ('--stats',))

    module.prune_archives(
        repository='repo',
        verbosity=VERBOSITY_SOME,
        retention_config=retention_config,
        command='attic',
    )


def test_prune_archives_with_verbosity_lots_should_call_attic_with_verbose_parameter():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(PRUNE_COMMAND + ('--verbose', '--stats',))

    module.prune_archives(
        repository='repo',
        verbosity=VERBOSITY_LOTS,
        retention_config=retention_config,
        command='attic',
    )


def test_parse_checks_returns_them_as_tuple():
    checks = module._parse_checks({'checks': 'foo disabled bar'})

    assert checks == ('foo', 'bar')


def test_parse_checks_with_missing_value_returns_defaults():
    checks = module._parse_checks({})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_blank_value_returns_defaults():
    checks = module._parse_checks({'checks': ''})

    assert checks == module.DEFAULT_CHECKS


def test_parse_checks_with_disabled_returns_no_checks():
    checks = module._parse_checks({'checks': 'disabled'})

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


def test_check_archives_should_call_attic_with_parameters():
    checks = flexmock()
    check_last = flexmock()
    consistency_config = flexmock().should_receive('get').and_return(check_last).mock
    flexmock(module).should_receive('_parse_checks').and_return(checks)
    flexmock(module).should_receive('_make_check_flags').with_args(checks, check_last).and_return(())
    stdout = flexmock()
    insert_subprocess_mock(
        ('attic', 'check', 'repo'),
        stdout=stdout,
    )
    insert_platform_mock()
    insert_datetime_mock()
    builtins_mock().should_receive('open').and_return(stdout)
    flexmock(module.os).should_receive('devnull')

    module.check_archives(
        verbosity=None,
        repository='repo',
        consistency_config=consistency_config,
        command='attic',
    )


def test_check_archives_with_verbosity_some_should_call_attic_with_verbose_parameter():
    consistency_config = flexmock().should_receive('get').and_return(None).mock
    flexmock(module).should_receive('_parse_checks').and_return(flexmock())
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_subprocess_mock(
        ('attic', 'check', 'repo', '--verbose'),
        stdout=None,
    )
    insert_platform_mock()
    insert_datetime_mock()

    module.check_archives(
        verbosity=VERBOSITY_SOME,
        repository='repo',
        consistency_config=consistency_config,
        command='attic',
    )


def test_check_archives_with_verbosity_lots_should_call_attic_with_verbose_parameter():
    consistency_config = flexmock().should_receive('get').and_return(None).mock
    flexmock(module).should_receive('_parse_checks').and_return(flexmock())
    flexmock(module).should_receive('_make_check_flags').and_return(())
    insert_subprocess_mock(
        ('attic', 'check', 'repo', '--verbose'),
        stdout=None,
    )
    insert_platform_mock()
    insert_datetime_mock()

    module.check_archives(
        verbosity=VERBOSITY_LOTS,
        repository='repo',
        consistency_config=consistency_config,
        command='attic',
    )


def test_check_archives_without_any_checks_should_bail():
    consistency_config = flexmock().should_receive('get').and_return(None).mock
    flexmock(module).should_receive('_parse_checks').and_return(())
    insert_subprocess_never()

    module.check_archives(
        verbosity=None,
        repository='repo',
        consistency_config=consistency_config,
        command='attic',
    )
