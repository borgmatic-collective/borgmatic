import sys

import pytest
from flexmock import flexmock

from borgmatic.actions import create as module


def test_create_borgmatic_manifest_creates_manifest_file():
    flexmock(module.os.path).should_receive('join').with_args(
        '/run/borgmatic', 'bootstrap', 'manifest.json'
    ).and_return('/run/borgmatic/bootstrap/manifest.json')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.os).should_receive('makedirs').and_return(True)

    flexmock(module.importlib.metadata).should_receive('version').and_return('1.0.0')
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/borgmatic/bootstrap/manifest.json', 'w'
    ).and_return(
        flexmock(
            __enter__=lambda *args: flexmock(write=lambda *args: None, close=lambda *args: None),
            __exit__=lambda *args: None,
        )
    )
    flexmock(module.json).should_receive('dump').and_return(True).once()

    module.create_borgmatic_manifest({}, 'test.yaml', '/run/borgmatic', False)


def test_create_borgmatic_manifest_creates_manifest_file_with_custom_borgmatic_runtime_directory():
    flexmock(module.os.path).should_receive('join').with_args(
        '/run/borgmatic', 'bootstrap', 'manifest.json'
    ).and_return('/run/borgmatic/bootstrap/manifest.json')
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.os).should_receive('makedirs').and_return(True)

    flexmock(module.importlib.metadata).should_receive('version').and_return('1.0.0')
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/borgmatic/bootstrap/manifest.json', 'w'
    ).and_return(
        flexmock(
            __enter__=lambda *args: flexmock(write=lambda *args: None, close=lambda *args: None),
            __exit__=lambda *args: None,
        )
    )
    flexmock(module.json).should_receive('dump').and_return(True).once()

    module.create_borgmatic_manifest(
        {'borgmatic_runtime_directory': '/borgmatic'}, 'test.yaml', '/run/borgmatic', False
    )


def test_create_borgmatic_manifest_does_not_create_manifest_file_on_dry_run():
    flexmock(module.json).should_receive('dump').never()

    module.create_borgmatic_manifest({}, 'test.yaml', '/run/borgmatic', True)


def test_expand_directory_with_basic_path_passes_it_through():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo')
    flexmock(module.glob).should_receive('glob').and_return([])

    paths = module.expand_directory('foo', None)

    assert paths == ['foo']


def test_expand_directory_with_glob_expands():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo*')
    flexmock(module.glob).should_receive('glob').and_return(['foo', 'food'])

    paths = module.expand_directory('foo*', None)

    assert paths == ['foo', 'food']


def test_expand_directory_with_working_directory_passes_it_through():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/foo').and_return([]).once()

    paths = module.expand_directory('foo', working_directory='/working/dir')

    assert paths == ['/working/dir/foo']


def test_expand_directory_with_glob_passes_through_working_directory():
    flexmock(module.os.path).should_receive('expanduser').and_return('foo*')
    flexmock(module.glob).should_receive('glob').with_args('/working/dir/foo*').and_return(
        ['/working/dir/foo', '/working/dir/food']
    ).once()

    paths = module.expand_directory('foo*', working_directory='/working/dir')

    assert paths == ['/working/dir/foo', '/working/dir/food']


def test_expand_directories_flattens_expanded_directories():
    flexmock(module).should_receive('expand_directory').with_args('~/foo', None).and_return(
        ['/root/foo']
    )
    flexmock(module).should_receive('expand_directory').with_args('bar*', None).and_return(
        ['bar', 'barf']
    )

    paths = module.expand_directories(('~/foo', 'bar*'))

    assert paths == ('/root/foo', 'bar', 'barf')


def test_expand_directories_with_working_directory_passes_it_through():
    flexmock(module).should_receive('expand_directory').with_args('foo', '/working/dir').and_return(
        ['/working/dir/foo']
    )

    paths = module.expand_directories(('foo',), working_directory='/working/dir')

    assert paths == ('/working/dir/foo',)


def test_expand_directories_considers_none_as_no_directories():
    paths = module.expand_directories(None, None)

    assert paths == ()


def test_map_directories_to_devices_gives_device_id_per_path():
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').and_return(flexmock(st_dev=66))

    device_map = module.map_directories_to_devices(('/foo', '/bar'))

    assert device_map == {
        '/foo': 55,
        '/bar': 66,
    }


def test_map_directories_to_devices_with_missing_path_does_not_error():
    flexmock(module.os.path).should_receive('exists').and_return(True).and_return(False)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/bar').never()

    device_map = module.map_directories_to_devices(('/foo', '/bar'))

    assert device_map == {
        '/foo': 55,
        '/bar': None,
    }


def test_map_directories_to_devices_uses_working_directory_to_construct_path():
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os).should_receive('stat').with_args('/foo').and_return(flexmock(st_dev=55))
    flexmock(module.os).should_receive('stat').with_args('/working/dir/bar').and_return(
        flexmock(st_dev=66)
    )

    device_map = module.map_directories_to_devices(
        ('/foo', 'bar'), working_directory='/working/dir'
    )

    assert device_map == {
        '/foo': 55,
        'bar': 66,
    }


@pytest.mark.parametrize(
    'directories,additional_directories,expected_directories',
    (
        ({'/': 1, '/root': 1}, {}, ['/']),
        ({'/': 1, '/root/': 1}, {}, ['/']),
        ({'/': 1, '/root': 2}, {}, ['/', '/root']),
        ({'/root': 1, '/': 1}, {}, ['/']),
        ({'/root': 1, '/root/foo': 1}, {}, ['/root']),
        ({'/root/': 1, '/root/foo': 1}, {}, ['/root/']),
        ({'/root': 1, '/root/foo/': 1}, {}, ['/root']),
        ({'/root': 1, '/root/foo': 2}, {}, ['/root', '/root/foo']),
        ({'/root/foo': 1, '/root': 1}, {}, ['/root']),
        ({'/root': None, '/root/foo': None}, {}, ['/root', '/root/foo']),
        ({'/root': 1, '/etc': 1, '/root/foo/bar': 1}, {}, ['/etc', '/root']),
        ({'/root': 1, '/root/foo': 1, '/root/foo/bar': 1}, {}, ['/root']),
        ({'/dup': 1, '/dup': 1}, {}, ['/dup']),
        ({'/foo': 1, '/bar': 1}, {}, ['/bar', '/foo']),
        ({'/foo': 1, '/bar': 2}, {}, ['/bar', '/foo']),
        ({'/root/foo': 1}, {'/root': 1}, []),
        ({'/root/foo': 1}, {'/root': 2}, ['/root/foo']),
        ({'/root/foo': 1}, {}, ['/root/foo']),
    ),
)
def test_deduplicate_directories_removes_child_paths_on_the_same_filesystem(
    directories, additional_directories, expected_directories
):
    assert (
        module.deduplicate_directories(directories, additional_directories) == expected_directories
    )


def test_pattern_root_directories_deals_with_none_patterns():
    assert module.pattern_root_directories(patterns=None) == []


def test_pattern_root_directories_parses_roots_and_ignores_others():
    assert module.pattern_root_directories(
        ['R /root', '+ /root/foo', '- /root/foo/bar', 'R /baz']
    ) == ['/root', '/baz']


def test_process_source_directories_includes_source_directories_and_config_paths():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working'
    )
    flexmock(module).should_receive('deduplicate_directories').and_return(
        ('foo', 'bar', 'test.yaml')
    )
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').with_args(
        ('foo', 'bar', 'test.yaml'), working_directory='/working'
    ).and_return(()).once()
    flexmock(module).should_receive('pattern_root_directories').and_return(())
    flexmock(module).should_receive('expand_directories').with_args(
        (), working_directory='/working'
    ).and_return(())

    assert module.process_source_directories(
        config={'source_directories': ['foo', 'bar']}, config_paths=('test.yaml',)
    ) == ('foo', 'bar', 'test.yaml')


def test_process_source_directories_does_not_include_config_paths_when_store_config_files_is_false():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working'
    )
    flexmock(module).should_receive('deduplicate_directories').and_return(('foo', 'bar'))
    flexmock(module).should_receive('map_directories_to_devices').and_return({})
    flexmock(module).should_receive('expand_directories').with_args(
        ('foo', 'bar'), working_directory='/working'
    ).and_return(()).once()
    flexmock(module).should_receive('pattern_root_directories').and_return(())
    flexmock(module).should_receive('expand_directories').with_args(
        (), working_directory='/working'
    ).and_return(())

    assert module.process_source_directories(
        config={'source_directories': ['foo', 'bar'], 'store_config_files': False},
        config_paths=('test.yaml',),
    ) == ('foo', 'bar')


def test_run_create_executes_and_calls_hooks_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module).should_receive('create_borgmatic_manifest').once()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module).should_receive('process_source_directories').and_return([])
    flexmock(module.os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        stats=flexmock(),
        json=False,
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            hook_context={},
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )


def test_run_create_with_store_config_files_false_does_not_create_borgmatic_manifest():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive('repositories_match').never()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module).should_receive('create_borgmatic_manifest').never()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module).should_receive('process_source_directories').and_return([])
    flexmock(module.os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        stats=flexmock(),
        json=False,
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={'store_config_files': False},
            config_paths=['/tmp/test.yaml'],
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
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once()
    flexmock(module).should_receive('create_borgmatic_manifest').once()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module).should_receive('process_source_directories').and_return([])
    flexmock(module.os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        stats=flexmock(),
        json=False,
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
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
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').never()
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').never()
    flexmock(module).should_receive('create_borgmatic_manifest').never()
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        stats=flexmock(),
        json=False,
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    list(
        module.run_create(
            config_filename='test.yaml',
            repository='repo',
            config={},
            config_paths=['/tmp/test.yaml'],
            hook_context={},
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    )


def test_run_create_produces_json():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.config.validate).should_receive(
        'repositories_match'
    ).once().and_return(True)
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.borg.create).should_receive('create_archive').once().and_return(
        flexmock()
    )
    parsed_json = flexmock()
    flexmock(module.borgmatic.actions.json).should_receive('parse_json').and_return(parsed_json)
    flexmock(module).should_receive('create_borgmatic_manifest').once()
    flexmock(module.borgmatic.hooks.command).should_receive('execute_hook').times(2)
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return({})
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).and_return({})
    flexmock(module).should_receive('process_source_directories').and_return([])
    flexmock(module.os.path).should_receive('join').and_return('/run/borgmatic/bootstrap')
    create_arguments = flexmock(
        repository=flexmock(),
        progress=flexmock(),
        stats=flexmock(),
        json=True,
        list_files=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    assert list(
        module.run_create(
            config_filename='test.yaml',
            repository={'path': 'repo'},
            config={},
            config_paths=['/tmp/test.yaml'],
            hook_context={},
            local_borg_version=None,
            create_arguments=create_arguments,
            global_arguments=global_arguments,
            dry_run_label='',
            local_path=None,
            remote_path=None,
        )
    ) == [parsed_json]
