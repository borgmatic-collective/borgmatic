import logging

from flexmock import flexmock

from borgmatic import hook as module


def test_interpolate_context_passes_through_command_without_variable():
    assert module.interpolate_context('ls', {'foo': 'bar'}) == 'ls'


def test_interpolate_context_passes_through_command_with_unknown_variable():
    assert module.interpolate_context('ls {baz}', {'foo': 'bar'}) == 'ls {baz}'


def test_interpolate_context_interpolates_variables():
    context = {'foo': 'bar', 'baz': 'quux'}

    assert module.interpolate_context('ls {foo}{baz} {baz}', context) == 'ls barquux quux'


def test_execute_hook_invokes_each_command():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda command, context: command
    )
    flexmock(module.execute).should_receive('execute_command').with_args(
        [':'], output_log_level=logging.WARNING, shell=True
    ).once()

    module.execute_hook([':'], None, 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_multiple_commands_invokes_each_command():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda command, context: command
    )
    flexmock(module.execute).should_receive('execute_command').with_args(
        [':'], output_log_level=logging.WARNING, shell=True
    ).once()
    flexmock(module.execute).should_receive('execute_command').with_args(
        ['true'], output_log_level=logging.WARNING, shell=True
    ).once()

    module.execute_hook([':', 'true'], None, 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_umask_sets_that_umask():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda command, context: command
    )
    flexmock(module.os).should_receive('umask').with_args(0o77).and_return(0o22).once()
    flexmock(module.os).should_receive('umask').with_args(0o22).once()
    flexmock(module.execute).should_receive('execute_command').with_args(
        [':'], output_log_level=logging.WARNING, shell=True
    )

    module.execute_hook([':'], 77, 'config.yaml', 'pre-backup', dry_run=False)


def test_execute_hook_with_dry_run_skips_commands():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda command, context: command
    )
    flexmock(module.execute).should_receive('execute_command').never()

    module.execute_hook([':', 'true'], None, 'config.yaml', 'pre-backup', dry_run=True)


def test_execute_hook_with_empty_commands_does_not_raise():
    module.execute_hook([], None, 'config.yaml', 'post-backup', dry_run=False)


def test_execute_hook_on_error_logs_as_error():
    flexmock(module).should_receive('interpolate_context').replace_with(
        lambda command, context: command
    )
    flexmock(module.execute).should_receive('execute_command').with_args(
        [':'], output_log_level=logging.ERROR, shell=True
    ).once()

    module.execute_hook([':'], None, 'config.yaml', 'on-error', dry_run=False)


def test_ping_healthchecks_hits_ping_url():
    ping_url = 'https://example.com'
    flexmock(module.requests).should_receive('get').with_args(ping_url)

    module.ping_healthchecks(ping_url, 'config.yaml', dry_run=False)


def test_ping_healthchecks_without_ping_url_does_not_raise():
    flexmock(module.requests).should_receive('get').never()

    module.ping_healthchecks(ping_url_or_uuid=None, config_filename='config.yaml', dry_run=False)


def test_ping_healthchecks_with_ping_uuid_hits_corresponding_url():
    ping_uuid = 'abcd-efgh-ijkl-mnop'
    flexmock(module.requests).should_receive('get').with_args(
        'https://hc-ping.com/{}'.format(ping_uuid)
    )

    module.ping_healthchecks(ping_uuid, 'config.yaml', dry_run=False)


def test_ping_healthchecks_hits_ping_url_with_append():
    ping_url = 'https://example.com'
    append = 'failed-so-hard'
    flexmock(module.requests).should_receive('get').with_args('{}/{}'.format(ping_url, append))

    module.ping_healthchecks(ping_url, 'config.yaml', dry_run=False, append=append)
