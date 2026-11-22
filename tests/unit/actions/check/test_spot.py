import pytest
from flexmock import flexmock

from borgmatic.actions.check import spot as module


def test_collect_spot_check_source_paths_parses_borg_output_and_includes_bootstrap_config_paths():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': True},
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config=object,
        patterns=object,
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=True,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_yield(
        'warning: stuff',
        '- /etc/path',
        '+ /etc/other',
        '? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={'working_directory': '/'},
        patterns=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/etc/path', '/etc/other')


def test_collect_spot_check_source_paths_omits_progress_from_create_dry_run_command():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': False},
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config={'working_directory': '/', 'progress': False, 'list_details': True},
        patterns=object,
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=False,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_yield(
        'warning: stuff',
        '- /etc/path',
        '+ /etc/other',
        '? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={'working_directory': '/', 'progress': True},
        patterns=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/etc/path', '/etc/other')


def test_collect_spot_check_source_paths_passes_through_stream_processes_false():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': False},
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config=object,
        patterns=object,
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=False,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_yield(
        'warning: stuff',
        '- /etc/path',
        '+ /etc/other',
        '? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={'working_directory': '/'},
        patterns=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/etc/path', '/etc/other')


def test_collect_spot_check_source_paths_without_working_directory_parses_borg_output():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': True},
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config=object,
        patterns=object,
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=True,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_yield(
        'warning: stuff',
        '- /etc/path',
        '+ /etc/other',
        '? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={},
        patterns=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/etc/path', '/etc/other')


def test_collect_spot_check_source_paths_skips_directories():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': True},
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config=object,
        patterns=object,
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=True,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_yield(
        'warning: stuff',
        '- /etc/path',
        '+ /etc/dir',
        '? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').with_args('/etc/path').and_return(False)
    flexmock(module.os.path).should_receive('isfile').with_args('/etc/dir').and_return(False)

    assert (
        module.collect_spot_check_source_paths(
            repository={'path': 'repo'},
            config={'working_directory': '/'},
            patterns=flexmock(),
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )
        == ()
    )


def test_collect_spot_check_archive_paths_excludes_directories_and_pipes():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/home/user/.borgmatic')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'type': 'f', 'path': 'etc/path'},
        {'type': 'p', 'path': 'var/pipe'},
        {'type': 'f', 'path': 'etc/other'},
        {'type': 'd', 'path': 'etc/dir'},
    )

    assert module.collect_spot_check_archive_paths(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/user/1001/borgmatic',
    ) == {'etc/path', 'etc/other'}


def test_collect_spot_check_archive_paths_excludes_file_in_borgmatic_runtime_directory_as_stored_with_prefix_truncation():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'type': 'f', 'path': 'etc/path'},
        {'type': 'f', 'path': 'borgmatic/some/thing'},
    )

    assert module.collect_spot_check_archive_paths(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/user/0/borgmatic',
    ) == {'etc/path'}


def test_collect_spot_check_archive_paths_excludes_file_in_borgmatic_source_directory():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/root/.borgmatic')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'type': 'f', 'path': 'etc/path'},
        {'type': 'f', 'path': 'root/.borgmatic/some/thing'},
    )

    assert module.collect_spot_check_archive_paths(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/user/0/borgmatic',
    ) == {'etc/path'}


def test_collect_spot_check_archive_paths_excludes_file_in_borgmatic_runtime_directory():
    flexmock(module.borgmatic.config.paths).should_receive(
        'get_borgmatic_source_directory',
    ).and_return('/root.borgmatic')
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'type': 'f', 'path': 'etc/path'},
        {'type': 'f', 'path': 'run/user/0/borgmatic/some/thing'},
    )

    assert module.collect_spot_check_archive_paths(
        repository={'path': 'repo'},
        archive='archive',
        config={},
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/user/0/borgmatic',
    ) == {'etc/path'}


def test_collect_spot_check_source_paths_uses_working_directory():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': True},
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config={'working_directory': '/working/dir', 'progress': False, 'list_details': True},
        patterns=object,
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=True,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_yield(
        'warning: stuff',
        '- foo',
        '+ bar',
        '? /nope',
    )
    flexmock(module.os.path).should_receive('isfile').with_args('/working/dir/foo').and_return(True)
    flexmock(module.os.path).should_receive('isfile').with_args('/working/dir/bar').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={'working_directory': '/working/dir'},
        patterns=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('foo', 'bar')


def test_collect_spot_check_source_paths_deduplicates_borg_output_paths():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hooks').and_return(
        {'hook1': False, 'hook2': True},
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.create).should_receive('make_base_create_command').with_args(
        dry_run=True,
        repository_path='repo',
        config=object,
        patterns=object,
        local_borg_version=object,
        global_arguments=object,
        borgmatic_runtime_directory='/run/borgmatic',
        local_path=object,
        remote_path=object,
        stream_processes=True,
    ).and_return((('borg', 'create'), ('repo::archive',), flexmock()))
    flexmock(module.borgmatic.borg.environment).should_receive('make_environment').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).and_yield(
        'warning: stuff',
        '- /etc/path',
        '+ /etc/other',
        '? /nope',
        '- /etc/path',
    )
    flexmock(module.os.path).should_receive('isfile').and_return(True)

    assert module.collect_spot_check_source_paths(
        repository={'path': 'repo'},
        config={'working_directory': '/'},
        patterns=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    ) == ('/etc/path', '/etc/other')


def test_compare_spot_check_hashes_returns_paths_having_failing_hashes():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_yield(
        'hash1  /foo',
        'hash2  /bar',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {},
        {'xxh64': 'nothash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/bar',)


def test_compare_spot_check_hashes_handles_weird_backslashed_hashes_from_xxh64sum():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_yield(
        '\\hash1  /foo',
        '\\hash2  /bar',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'nothash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/bar',)


def test_compare_spot_check_hashes_handles_incorrect_path_names_from_xxh64sum():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_yield(
        'hash1  /foo/wrong/path',
        'hash2  /bar/wrong/path',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'nothash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/bar',)


def test_compare_spot_check_hashes_with_xxh64sum_failure_falls_back_to_individual_file_hashing():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_raise(
        module.subprocess.CalledProcessError(1, 'wtf')
    )
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo'), working_directory=None).and_raise(
        module.subprocess.CalledProcessError(1, 'wtf')
    ).once()
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/bar'), working_directory=None).and_yield(
        'hash2  /bar',
    ).once()

    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'hash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/foo',)


def test_compare_spot_check_hashes_returns_relative_paths_having_failing_hashes():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', 'foo', 'bar'), working_directory=None).and_yield(
        'hash1  foo',
        'hash2  bar',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'nothash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('foo', 'bar', 'baz', 'quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('bar',)


def test_compare_spot_check_hashes_handles_data_sample_percentage_above_100():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_yield(
        'hash1  /foo',
        'hash2  /bar',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'nothash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'nothash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 1000,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar'),
        archive_paths={'foo', 'bar'},
        source_to_archive_root_paths=(('/foo', 'foo'), ('/bar', 'bar')),
    ) == ('/foo', '/bar')


def test_compare_spot_check_hashes_uses_xxh64sum_command_option():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(
        ('/usr/local/bin/xxhsum', '-H64', '/foo', '/bar'),
        working_directory=None,
    ).and_yield('hash1  /foo', 'hash2  /bar')
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'nothash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                    'xxh64sum_command': '/usr/local/bin/xxhsum -H64',
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/bar',)


def test_compare_spot_check_hashes_considers_path_missing_from_archive_as_not_matching():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_yield(
        'hash1  /foo',
        'hash2  /bar',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''}
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/bar',)


def test_compare_spot_check_hashes_skips_hardlink_path_in_archive():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo', '/bar', '/hard/./link'), working_directory=None).and_yield(
        'hash1  /foo',
        'hash2  /bar',
        'hash1  /hard/./link',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.split('/./')[-1].lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'hash2', 'path': 'bar', 'linktarget': ''},
        {'xxh64': '', 'path': 'link', 'linktarget': 'foo'},
    )

    assert (
        module.compare_spot_check_hashes(
            repository={'path': 'repo'},
            archive='archive',
            config={
                'checks': [
                    {
                        'name': 'spot',
                        'data_sample_percentage': 100,
                    },
                ],
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            source_paths=('/foo', '/bar', '/hard/./link'),
            archive_paths={'foo', 'bar', 'link'},
            source_to_archive_root_paths=(('/foo', 'foo'), ('/bar', 'bar'), ('/hard/link', 'link')),
        )
        == ()
    )


def test_compare_spot_check_hashes_considers_symlink_path_as_not_matching():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').with_args('/foo').and_return(False)
    flexmock(module.os.path).should_receive('islink').with_args('/bar').and_return(True)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo'), working_directory=None).and_yield('hash1  /foo')
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'hash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/bar',)


def test_compare_spot_check_hashes_considers_borg_2_symlink_path_as_not_matching():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').with_args('/foo').and_return(False)
    flexmock(module.os.path).should_receive('islink').with_args('/bar').and_return(True)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo'), working_directory=None).and_yield('hash1  /foo')
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'target': ''},
        {'xxh64': 'hash2', 'path': 'bar', 'target': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/bar',)


def test_compare_spot_check_hashes_considers_non_existent_path_as_not_matching():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').with_args('/foo').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/bar').and_return(False)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo'), working_directory=None).and_yield('hash1  /foo')
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'hash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/bar',)


def test_compare_spot_check_hashes_with_too_many_paths_feeds_them_to_commands_in_chunks():
    flexmock(module).SAMPLE_PATHS_SUBSET_COUNT = 2
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/foo', '/bar'), working_directory=None).and_yield(
        'hash1  /foo',
        'hash2  /bar',
    )
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/baz', '/quux'), working_directory=None).and_yield(
        'hash3  /baz',
        'hash4  /quux',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'hash2', 'path': 'bar', 'linktarget': ''},
    ).and_yield(
        {'xxh64': 'hash3', 'path': 'baz', 'linktarget': ''},
        {'xxh64': 'nothash4', 'path': 'quux', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 100,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/foo', '/bar', '/baz', '/quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/quux',)


def test_compare_spot_check_hashes_uses_working_directory_to_access_source_paths():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/working/dir',
    )
    flexmock(module.os.path).should_receive('exists').with_args('/working/dir/foo').and_return(True)
    flexmock(module.os.path).should_receive('exists').with_args('/working/dir/bar').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', 'foo', 'bar'), working_directory='/working/dir').and_yield(
        'hash1  foo',
        'hash2  bar',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path)
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {'xxh64': 'nothash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
            'working_directory': '/working/dir',
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('foo', 'bar', 'baz', 'quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('foo', 'foo'),
            ('bar', 'bar'),
            ('baz', 'baz'),
            ('quux', 'quux'),
        ),
    ) == ('bar',)


def test_compare_spot_check_hashes_with_slashdot_hack_returns_paths_having_failing_hashes():
    flexmock(module.random).should_receive('SystemRandom').and_return(
        flexmock(sample=lambda population, count: population[:count]),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module.os.path).should_receive('islink').and_return(False)
    flexmock(module.borgmatic.execute).should_receive(
        'execute_command_and_capture_output',
    ).with_args(('xxh64sum', '/base/./foo', '/base/./bar'), working_directory=None).and_yield(
        'hash1  /base/./foo',
        'hash2  /base/./bar',
    )
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.split('/./')[-1].lstrip('/'))
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'xxh64': 'hash1', 'path': 'foo', 'linktarget': ''},
        {},
        {'xxh64': 'nothash2', 'path': 'bar', 'linktarget': ''},
    )

    assert module.compare_spot_check_hashes(
        repository={'path': 'repo'},
        archive='archive',
        config={
            'checks': [
                {
                    'name': 'archives',
                    'frequency': '2 weeks',
                },
                {
                    'name': 'spot',
                    'data_sample_percentage': 50,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        source_paths=('/base/./foo', '/base/./bar', '/other/./baz', '/other/./quux'),
        archive_paths={'foo', 'bar', 'baz', 'quux'},
        source_to_archive_root_paths=(
            ('/foo', 'foo'),
            ('/bar', 'bar'),
            ('/baz', 'baz'),
            ('/quux', 'quux'),
        ),
    ) == ('/base/./bar',)


def test_spot_check_without_spot_configuration_errors():
    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'archives',
                    },
                ],
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_spot_check_without_any_configuration_errors():
    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={},
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_spot_check_data_tolerance_percentage_greater_than_data_sample_percentage_errors():
    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'spot',
                        'data_tolerance_percentage': 7,
                        'data_sample_percentage': 5,
                    },
                ],
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_spot_check_with_count_delta_greater_than_count_tolerance_percentage_errors():
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'collect_and_process_patterns'
    ).and_return(flexmock())
    flexmock(module).should_receive('collect_spot_check_source_paths').and_return(
        ('/foo', '/bar', '/baz', '/quux'),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive',
    )
    flexmock(module).should_receive('collect_spot_check_archive_paths').and_return(
        ('/foo', '/bar'),
    ).once()
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'make_source_to_archive_root_map'
    ).and_return(flexmock())
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'map_source_path_to_archive_path'
    ).replace_with(lambda source_path, *other: source_path.lstrip('/'))

    with pytest.raises(ValueError) as error:
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'spot',
                        'count_tolerance_percentage': 1,
                        'data_tolerance_percentage': 4,
                        'data_sample_percentage': 5,
                    },
                ],
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )

    assert (
        str(error.value)
        == 'Spot check failed\n50.00% file count delta between source paths (4 total) and latest archive (2 total); tolerance is 1%\nOnly in source paths: /foo, /bar, /baz, /quux\nOnly in latest archive: /bar, /foo'
    )


def test_spot_check_with_failing_percentage_greater_than_data_tolerance_percentage_errors():
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'collect_and_process_patterns'
    ).and_return(flexmock())
    flexmock(module).should_receive('collect_spot_check_source_paths').and_return(
        ('/foo', '/bar', '/baz', '/quux'),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive',
    )
    flexmock(module).should_receive('collect_spot_check_archive_paths').and_return(('/foo', '/bar'))
    flexmock(module).should_receive('compare_spot_check_hashes').and_return(
        ('/bar', '/baz', '/quux'),
    ).once()
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'make_source_to_archive_root_map'
    ).and_return(flexmock())

    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'spot',
                        'count_tolerance_percentage': 55,
                        'data_tolerance_percentage': 4,
                        'data_sample_percentage': 5,
                    },
                ],
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )


def test_spot_check_with_high_enough_tolerances_does_not_raise():
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'collect_and_process_patterns'
    ).and_return(flexmock())
    flexmock(module).should_receive('collect_spot_check_source_paths').and_return(
        ('/foo', '/bar', '/baz', '/quux'),
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive',
    )
    flexmock(module).should_receive('collect_spot_check_archive_paths').and_return(('/foo', '/bar'))
    flexmock(module).should_receive('compare_spot_check_hashes').and_return(
        ('/bar', '/baz', '/quux'),
    ).once()
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'make_source_to_archive_root_map'
    ).and_return(flexmock())

    module.spot_check(
        repository={'path': 'repo'},
        config={
            'checks': [
                {
                    'name': 'spot',
                    'count_tolerance_percentage': 55,
                    'data_tolerance_percentage': 80,
                    'data_sample_percentage': 80,
                },
            ],
        },
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        local_path=flexmock(),
        remote_path=flexmock(),
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_spot_check_without_any_source_paths_errors():
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'collect_and_process_patterns'
    ).and_return(flexmock())
    flexmock(module).should_receive('collect_spot_check_source_paths').and_return(())
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive',
    )
    flexmock(module).should_receive('collect_spot_check_archive_paths').and_return(('/foo', '/bar'))
    flexmock(module.borgmatic.actions.check.paths).should_receive(
        'make_source_to_archive_root_map'
    ).never()
    flexmock(module).should_receive('compare_spot_check_hashes').never()

    with pytest.raises(ValueError):
        module.spot_check(
            repository={'path': 'repo'},
            config={
                'checks': [
                    {
                        'name': 'spot',
                        'count_tolerance_percentage': 10,
                        'data_tolerance_percentage': 40,
                        'data_sample_percentage': 50,
                    },
                ],
            },
            local_borg_version=flexmock(),
            global_arguments=flexmock(),
            local_path=flexmock(),
            remote_path=flexmock(),
            borgmatic_runtime_directory='/run/borgmatic',
        )
