import sys
from flexmock import flexmock

from borgmatic.actions import create as module


def test_run_create_executes_and_calls_hooks_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module).should_receive('create_borgmatic_manifest').once()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    create_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        stats=flexmock(),
        json=flexmock(),
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False, used_config_paths=[])

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
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


def test_run_create_runs_with_selected_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module).should_receive('create_borgmatic_manifest').once()
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        stats=flexmock(),
        json=flexmock(),
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False, used_config_paths=[])

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
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


def test_run_create_bails_if_repository_does_not_match():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(False)
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').never()
    flexmock(module).should_receive('create_borgmatic_manifest').never()
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        stats=flexmock(),
        json=flexmock(),
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False, used_config_paths=[])

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


def test_create_borgmatic_manifest_creates_manifest_file():
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.os).should_receive('makedirs').and_return(True)

    flexmock(module.importlib_metadata).should_receive('version').and_return('1.0.0')
    flexmock(module.json).should_receive('dump').and_return(True)

    module.create_borgmatic_manifest({}, 'test.yaml', False)


def test_create_borgmatic_manifest_creates_manifest_file_with_custom_borgmatic_source_directory():
    flexmock(module.os.path).should_receive('join').with_args(
        '/borgmatic', 'bootstrap', 'manifest.json'
    ).and_return('/borgmatic/bootstrap/manifest.json')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.os).should_receive('makedirs').and_return(True)

    flexmock(module.importlib_metadata).should_receive('version').and_return('1.0.0')
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/borgmatic/bootstrap/manifest.json', 'w'
    ).and_return(
        flexmock(
            __enter__=lambda *args: flexmock(
                write=lambda *args: None, close=lambda *args: None
            ),
            __exit__=lambda *args: None,
        )
    )
    flexmock(module.json).should_receive('dump').and_return(True)

    module.create_borgmatic_manifest(
        {'borgmatic_source_directory': '/borgmatic'}, 'test.yaml', False
    )


def test_create_borgmatic_manifest_does_not_create_manifest_file_on_dry_run():
    flexmock(module.os.path).should_receive('expanduser').never()

    module.create_borgmatic_manifest({}, 'test.yaml', True)
