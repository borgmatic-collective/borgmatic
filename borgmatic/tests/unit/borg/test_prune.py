from collections import OrderedDict

from flexmock import flexmock

from borgmatic.borg import prune as module
from borgmatic.verbosity import VERBOSITY_SOME, VERBOSITY_LOTS


def insert_subprocess_mock(check_call_command, **kwargs):
    subprocess = flexmock(module.subprocess)
    subprocess.should_receive('check_call').with_args(check_call_command, **kwargs).once()


BASE_PRUNE_FLAGS = (
    ('--keep-daily', '1'),
    ('--keep-weekly', '2'),
    ('--keep-monthly', '3'),
)


def test_make_prune_flags_should_return_flags_from_config_plus_default_prefix():
    retention_config = OrderedDict(
        (
            ('keep_daily', 1),
            ('keep_weekly', 2),
            ('keep_monthly', 3),
        )
    )

    result = module._make_prune_flags(retention_config)

    assert tuple(result) == BASE_PRUNE_FLAGS + (('--prefix', '{hostname}-'),)


def test_make_prune_flags_accepts_prefix_with_placeholders():
    retention_config = OrderedDict(
        (
            ('keep_daily', 1),
            ('prefix', 'Documents_{hostname}-{now}'),
        )
    )

    result = module._make_prune_flags(retention_config)

    expected = (
        ('--keep-daily', '1'),
        ('--prefix', 'Documents_{hostname}-{now}'),
    )

    assert tuple(result) == expected


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
    )


def test_prune_archives_with_verbosity_lots_should_call_borg_with_debug_parameter():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(PRUNE_COMMAND + ('--debug', '--stats', '--list'))

    module.prune_archives(
        repository='repo',
        verbosity=VERBOSITY_LOTS,
        retention_config=retention_config,
    )


def test_prune_archives_with_remote_path_should_call_borg_with_remote_path_parameters():
    retention_config = flexmock()
    flexmock(module).should_receive('_make_prune_flags').with_args(retention_config).and_return(
        BASE_PRUNE_FLAGS,
    )
    insert_subprocess_mock(PRUNE_COMMAND + ('--remote-path', 'borg1'))

    module.prune_archives(
        verbosity=None,
        repository='repo',
        retention_config=retention_config,
        remote_path='borg1',
    )
