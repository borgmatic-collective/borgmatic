from flexmock import flexmock

from borgmatic.actions import create as module


def test_run_create_executes_and_calls_hooks():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.create).should_receive('create_archive')
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    create_arguments = flexmock(
        progress=flexmock(), stats=flexmock(), json=flexmock(), list_files=flexmock()
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository='repo',
            location={},
            storage={},
            hooks={},
            hook_context={},
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )
