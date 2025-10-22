import sys

from flexmock import flexmock

from borgmatic.hooks.data_source import bootstrap as module


def test_dump_data_sources_creates_manifest_file():
    flexmock(module.os).should_receive('makedirs')

    flexmock(module.importlib.metadata).should_receive('version').and_return('1.0.0')
    manifest_file = flexmock(
        __enter__=lambda *args: flexmock(write=lambda *args: None, close=lambda *args: None),
        __exit__=lambda *args: None,
    )
    flexmock(sys.modules['builtins']).should_receive('open').with_args(
        '/run/borgmatic/bootstrap/manifest.json',
        'w',
        encoding='utf-8',
    ).and_return(manifest_file)
    flexmock(module.json).should_receive('dump').with_args(
        {'borgmatic_version': '1.0.0', 'config_paths': ('test.yaml',)},
        manifest_file,
    ).once()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').with_args(
        object,
        module.borgmatic.borg.pattern.Pattern(
            '/run/borgmatic/bootstrap', source=module.borgmatic.borg.pattern.Pattern_source.HOOK
        ),
    ).once()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').with_args(
        object,
        module.borgmatic.borg.pattern.Pattern(
            'test.yaml', source=module.borgmatic.borg.pattern.Pattern_source.HOOK
        ),
    ).once()

    module.dump_data_sources(
        hook_config=None,
        config={},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=False,
    )


def test_dump_data_sources_with_store_config_files_false_does_not_create_manifest_file():
    flexmock(module.os).should_receive('makedirs').never()
    flexmock(module.json).should_receive('dump').never()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').never()
    hook_config = {'store_config_files': False}

    module.dump_data_sources(
        hook_config=hook_config,
        config={'bootstrap': hook_config},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=True,
    )


def test_dump_data_sources_with_dry_run_does_not_create_manifest_file():
    flexmock(module.os).should_receive('makedirs').never()
    flexmock(module.json).should_receive('dump').never()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').never()
    module.dump_data_sources(
        hook_config=None,
        config={},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=True,
    )


def test_remove_data_source_dumps_deletes_manifest_and_parent_directory():
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os).should_receive('remove').with_args(
        '/run/borgmatic/bootstrap/manifest.json',
    ).once()
    flexmock(module.os).should_receive('rmdir').with_args('/run/borgmatic/bootstrap').once()

    module.remove_data_source_dumps(
        hook_config=None,
        config={},
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_dumps_with_dry_run_bails():
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os).should_receive('remove').never()
    flexmock(module.os).should_receive('rmdir').never()

    module.remove_data_source_dumps(
        hook_config=None,
        config={},
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=True,
    )


def test_remove_data_source_dumps_swallows_manifest_file_not_found_error():
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os).should_receive('remove').with_args(
        '/run/borgmatic/bootstrap/manifest.json',
    ).and_raise(FileNotFoundError).once()
    flexmock(module.os).should_receive('rmdir').with_args('/run/borgmatic/bootstrap').once()

    module.remove_data_source_dumps(
        hook_config=None,
        config={},
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )


def test_remove_data_source_dumps_swallows_manifest_parent_directory_not_found_error():
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob',
    ).and_return('/run/borgmatic')
    flexmock(module.glob).should_receive('glob').replace_with(lambda path: [path])
    flexmock(module.os).should_receive('remove').with_args(
        '/run/borgmatic/bootstrap/manifest.json',
    ).once()
    flexmock(module.os).should_receive('rmdir').with_args('/run/borgmatic/bootstrap').and_raise(
        FileNotFoundError,
    ).once()

    module.remove_data_source_dumps(
        hook_config=None,
        config={},
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=flexmock(),
        dry_run=False,
    )
