import io
import sys

import pytest
from flexmock import flexmock

from borgmatic.hooks.data_source import dump as module


def test_make_data_source_dump_path_joins_arguments():
    assert module.make_data_source_dump_path('/tmp', 'super_databases') == '/tmp/super_databases'


def test_make_data_source_dump_filename_uses_name_and_hostname():
    assert (
        module.make_data_source_dump_filename('databases', 'test', 'hostname')
        == 'databases/hostname/test'
    )


def test_make_data_source_dump_filename_uses_name_and_hostname_and_port():
    assert (
        module.make_data_source_dump_filename('databases', 'test', 'hostname', 1234)
        == 'databases/hostname:1234/test'
    )


def test_make_data_source_dump_filename_uses_label():
    assert (
        module.make_data_source_dump_filename(
            'databases', 'test', 'hostname', 1234, label='custom_label'
        )
        == 'databases/custom_label/test'
    )


def test_make_data_source_dump_filename_uses_container():
    assert (
        module.make_data_source_dump_filename(
            'databases', 'test', 'hostname', 1234, container='container'
        )
        == 'databases/container:1234/test'
    )


def test_make_data_source_dump_filename_without_hostname_defaults_to_localhost():
    assert module.make_data_source_dump_filename('databases', 'test') == 'databases/localhost/test'


def test_make_data_source_dump_filename_with_invalid_name_raises():
    with pytest.raises(ValueError):
        module.make_data_source_dump_filename('databases', 'invalid/name')


def test_write_data_source_dumps_metadata_writes_json_to_file():
    dumps_metadata = [
        module.borgmatic.actions.restore.Dump('databases', 'foo'),
        module.borgmatic.actions.restore.Dump('databases', 'bar'),
    ]
    dumps_stream = io.StringIO('password')
    dumps_stream.name = '/run/borgmatic/databases/dumps.json'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args(dumps_stream.name, 'w', encoding='utf-8').and_return(
        dumps_stream
    )
    flexmock(dumps_stream).should_receive('close')  # Prevent close() so getvalue() below works.

    module.write_data_source_dumps_metadata('/run/borgmatic', 'databases', dumps_metadata)

    assert (
        dumps_stream.getvalue()
        == '{"dumps": [{"container": null, "data_source_name": "foo", "hook_name": "databases", "hostname": null, "label": null, "port": null}, {"container": null, "data_source_name": "bar", "hook_name": "databases", "hostname": null, "label": null, "port": null}]}'
    )


def test_write_data_source_dumps_metadata_with_operating_system_error_raises():
    dumps_metadata = [
        module.borgmatic.actions.restore.Dump('databases', 'foo'),
        module.borgmatic.actions.restore.Dump('databases', 'bar'),
    ]
    dumps_stream = io.StringIO('password')
    dumps_stream.name = '/run/borgmatic/databases/dumps.json'
    builtins = flexmock(sys.modules['builtins'])
    builtins.should_receive('open').with_args(dumps_stream.name, 'w', encoding='utf-8').and_raise(
        OSError
    )

    with pytest.raises(ValueError):
        module.write_data_source_dumps_metadata('/run/borgmatic', 'databases', dumps_metadata)


def test_parse_data_source_dumps_metadata_converts_json_to_dump_instances():
    dumps_json = '{"dumps": [{"data_source_name": "foo", "hook_name": "databases", "hostname": null, "port": null}, {"data_source_name": "bar", "hook_name": "databases", "hostname": "example.org", "port": 1234}]}'

    assert module.parse_data_source_dumps_metadata(
        dumps_json, 'borgmatic/databases/dumps.json'
    ) == (
        module.borgmatic.actions.restore.Dump('databases', 'foo'),
        module.borgmatic.actions.restore.Dump('databases', 'bar', 'example.org', 1234),
    )


def test_parse_data_source_dumps_metadata_with_invalid_json_raises():
    with pytest.raises(ValueError):
        module.parse_data_source_dumps_metadata('[{', 'borgmatic/databases/dumps.json')


def test_parse_data_source_dumps_metadata_with_unknown_keys_raises():
    dumps_json = (
        '{"dumps": [{"data_source_name": "foo", "hook_name": "databases", "wtf": "is this"}]}'
    )

    with pytest.raises(ValueError):
        module.parse_data_source_dumps_metadata(dumps_json, 'borgmatic/databases/dumps.json')


def test_parse_data_source_dumps_metadata_with_missing_dumps_key_raises():
    dumps_json = '{"not": "what we are looking for"}'

    with pytest.raises(ValueError):
        module.parse_data_source_dumps_metadata(dumps_json, 'borgmatic/databases/dumps.json')


def test_create_parent_directory_for_dump_does_not_raise():
    flexmock(module.os).should_receive('makedirs')

    module.create_parent_directory_for_dump('/path/to/parent')


def test_create_named_pipe_for_dump_does_not_raise():
    flexmock(module).should_receive('create_parent_directory_for_dump')
    flexmock(module.os).should_receive('mkfifo')

    module.create_named_pipe_for_dump('/path/to/pipe')


def test_remove_data_source_dumps_removes_dump_path():
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return(flexmock())
    flexmock(module.glob).should_receive('glob').and_return(['databases', 'other'])
    flexmock(module.shutil).should_receive('rmtree').with_args(
        'databases', ignore_errors=True
    ).once()
    flexmock(module.shutil).should_receive('rmtree').with_args('other', ignore_errors=True).once()

    module.remove_data_source_dumps('databases', 'SuperDB', dry_run=False)


def test_remove_data_source_dumps_with_dry_run_skips_removal():
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return(flexmock())
    flexmock(module.glob).should_receive('glob').and_return(['databases', 'other'])
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps('databases', 'SuperDB', dry_run=True)


def test_remove_data_source_dumps_with_non_existent_dump_path_skips_removal():
    flexmock(module.borgmatic.config.paths).should_receive(
        'replace_temporary_subdirectory_with_glob'
    ).and_return(flexmock())
    flexmock(module.glob).should_receive('glob').and_return([])
    flexmock(module.shutil).should_receive('rmtree').never()

    module.remove_data_source_dumps('databases', 'SuperDB', dry_run=False)


def test_convert_glob_patterns_to_borg_pattern_makes_multipart_regular_expression():
    assert (
        module.convert_glob_patterns_to_borg_pattern(('/etc/foo/bar', '/bar/baz/quux'))
        == 're:(?s:etc/foo/bar)$|(?s:etc/foo/bar/.*)$|(?s:bar/baz/quux)$|(?s:bar/baz/quux/.*)$'
    )


def test_strip_path_prefix_from_extracted_dump_destination_renames_first_matching_databases_subdirectory():
    flexmock(module.os).should_receive('walk').and_return(
        [
            ('/foo', flexmock(), flexmock()),
            ('/foo/bar', flexmock(), flexmock()),
            ('/foo/bar/postgresql_databases', flexmock(), flexmock()),
            ('/foo/bar/mariadb_databases', flexmock(), flexmock()),
        ],
    )

    flexmock(module.shutil).should_receive('rmtree')
    flexmock(module.shutil).should_receive('move').with_args(
        '/foo/bar/postgresql_databases',
        '/run/user/0/borgmatic/postgresql_databases',
    ).once()
    flexmock(module.shutil).should_receive('move').with_args(
        '/foo/bar/mariadb_databases',
        '/run/user/0/borgmatic/mariadb_databases',
    ).never()

    module.strip_path_prefix_from_extracted_dump_destination(
        '/foo', 'postgresql_databases', '/run/user/0/borgmatic'
    )


def test_extract_dump_returns_extract_process():
    flexmock(module.tempfile).should_receive('mkdtemp').never()
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'convert_glob_patterns_to_borg_pattern',
    ).and_return(flexmock())
    extract_process = flexmock()
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process,
    ).once()
    flexmock(module).should_receive('strip_path_prefix_from_extracted_dump_destination').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    assert (
        module.extract_dump(
            repository={'path': 'repo.borg'},
            config=flexmock(),
            local_borg_version=flexmock(),
            global_arguments=flexmock(dry_run=False),
            local_path=flexmock(),
            remote_path=flexmock(),
            archive_name=flexmock(),
            hook_name=flexmock(),
            data_source={'name': 'foo'},
            borgmatic_runtime_directory='/run/borgmatic',
            dump_patterns=flexmock(),
        )
        == extract_process
    )


def test_extract_dump_with_directory_format_cleans_up_destination_path():
    flexmock(module.tempfile).should_receive('mkdtemp').once().and_return(
        '/run/user/0/borgmatic/tmp1234',
    )
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'convert_glob_patterns_to_borg_pattern',
    ).and_return(flexmock())
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        None,
    ).once()
    flexmock(module).should_receive('strip_path_prefix_from_extracted_dump_destination').once()
    flexmock(module.shutil).should_receive('rmtree').once()

    assert (
        module.extract_dump(
            repository={'path': 'repo.borg'},
            config=flexmock(),
            local_borg_version=flexmock(),
            global_arguments=flexmock(dry_run=False),
            local_path=flexmock(),
            remote_path=flexmock(),
            archive_name=flexmock(),
            hook_name=flexmock(),
            data_source={'name': 'foo', 'format': 'directory'},
            borgmatic_runtime_directory='/run/borgmatic',
            dump_patterns=flexmock(),
        )
        is None
    )


def test_extract_dump_with_directory_format_dump_error_cleans_up_destination_path():
    flexmock(module.tempfile).should_receive('mkdtemp').once().and_return(
        '/run/user/0/borgmatic/tmp1234',
    )
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'convert_glob_patterns_to_borg_pattern',
    ).and_return(flexmock())
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_raise(
        ValueError,
    ).once()
    flexmock(module).should_receive('strip_path_prefix_from_extracted_dump_destination').never()
    flexmock(module.shutil).should_receive('rmtree').once()

    with pytest.raises(ValueError):
        assert (
            module.extract_dump(
                repository={'path': 'repo.borg'},
                config=flexmock(),
                local_borg_version=flexmock(),
                global_arguments=flexmock(dry_run=False),
                local_path=flexmock(),
                remote_path=flexmock(),
                archive_name=flexmock(),
                hook_name=flexmock(),
                data_source={'name': 'foo', 'format': 'directory'},
                borgmatic_runtime_directory='/run/borgmatic',
                dump_patterns=flexmock(),
            )
            is None
        )


def test_extract_dump_with_directory_format_and_dry_run_skips_directory_move_and_cleanup():
    flexmock(module.tempfile).should_receive('mkdtemp').once().and_return('/run/borgmatic/tmp1234')
    flexmock(module.borgmatic.hooks.data_source.dump).should_receive(
        'convert_glob_patterns_to_borg_pattern',
    ).and_return(flexmock())
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        None,
    ).once()
    flexmock(module).should_receive('strip_path_prefix_from_extracted_dump_destination').never()
    flexmock(module.shutil).should_receive('rmtree').never()

    assert (
        module.extract_dump(
            repository={'path': 'repo.borg'},
            config=flexmock(),
            local_borg_version=flexmock(),
            global_arguments=flexmock(dry_run=True),
            local_path=flexmock(),
            remote_path=flexmock(),
            archive_name=flexmock(),
            hook_name=flexmock(),
            data_source={'name': 'foo', 'format': 'directory'},
            borgmatic_runtime_directory='/run/borgmatic',
            dump_patterns=flexmock(),
        )
        is None
    )
