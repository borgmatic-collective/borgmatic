import logging

from flexmock import flexmock

from borgmatic.hooks.data_source import openldap as module

from ...test_verbosity import insert_logging_mock


def test_use_streaming_true_for_any_databases():
    assert module.use_streaming(
        databases=[flexmock(), flexmock()],
        config=flexmock(),
    )


def test_use_streaming_false_for_no_databases():
    assert not module.use_streaming(databases=[], config=flexmock())


def test_make_debug_flags_with_debug_log_level_returns_full_debug_flag():
    insert_logging_mock(logging.DEBUG)

    assert module.make_debug_flags() == ('-d', '65535')


def test_make_debug_flags_with_info_log_level_returns_stats_debug_flag():
    insert_logging_mock(logging.INFO)

    assert module.make_debug_flags() == ('-d', '256')


def test_make_debug_flags_with_warning_log_level_returns_no_flags():
    insert_logging_mock(logging.WARNING)

    assert module.make_debug_flags() == ()


def test_build_dump_command_selects_database_by_suffix():
    flexmock(module).should_receive('make_debug_flags').and_return(())

    assert module.build_dump_command(
        {'name': 'dc=example,dc=com'},
        '/run/borgmatic/dump',
    ) == ('slapcat', '-b', 'dc=example,dc=com', '-l', '/run/borgmatic/dump')


def test_build_dump_command_with_slapcat_command_uses_it():
    flexmock(module).should_receive('make_debug_flags').and_return(())

    assert module.build_dump_command(
        {'name': 'dc=example,dc=com', 'slapcat_command': '/usr/sbin/slapcat -c'},
        '/run/borgmatic/dump',
    ) == ('/usr/sbin/slapcat', '-c', '-b', 'dc=example,dc=com', '-l', '/run/borgmatic/dump')


def test_build_dump_command_passes_shell_metacharacters_through_literally():
    flexmock(module).should_receive('make_debug_flags').and_return(())

    # The dump command runs without a shell, so a metacharacter is just a literal argument with
    # nothing to inject into. Escaping it here would corrupt commands at paths containing spaces.
    assert module.build_dump_command(
        {'name': 'dc=example,dc=com', 'slapcat_command': 'slapcat *'},
        '/run/borgmatic/dump',
    ) == ('slapcat', '*', '-b', 'dc=example,dc=com', '-l', '/run/borgmatic/dump')


def test_build_dump_command_with_space_in_suffix_passes_it_through():
    flexmock(module).should_receive('make_debug_flags').and_return(())

    # LDAP suffixes legitimately contain spaces, so escaping the name would corrupt it.
    assert module.build_dump_command(
        {'name': 'o=Example Corp,dc=example,dc=com'},
        '/run/borgmatic/dump',
    ) == (
        'slapcat',
        '-b',
        'o=Example Corp,dc=example,dc=com',
        '-l',
        '/run/borgmatic/dump',
    )


def test_build_dump_command_includes_debug_flags():
    flexmock(module).should_receive('make_debug_flags').and_return(('-d', '256'))

    assert module.build_dump_command(
        {'name': 'dc=example,dc=com'},
        '/run/borgmatic/dump',
    ) == ('slapcat', '-d', '256', '-b', 'dc=example,dc=com', '-l', '/run/borgmatic/dump')


def test_dump_data_sources_logs_and_skips_if_dump_already_exists():
    databases = [{'name': 'dc=example,dc=com'}]

    flexmock(module).should_receive('make_dump_path').and_return('/run/borgmatic')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/run/borgmatic/dump',
    )
    flexmock(module.os.path).should_receive('exists').and_return(True)
    flexmock(module).should_receive('build_dump_command').never()
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/run/borgmatic',
        'openldap_databases',
        [
            module.borgmatic.actions.restore.Dump('openldap_databases', 'dc=example,dc=com'),
        ],
    ).once()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').with_args(
        object,
        module.borgmatic.borg.pattern.Pattern(
            '/run/borgmatic/openldap_databases',
            source=module.borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
    ).once()

    assert (
        module.dump_data_sources(
            databases,
            {},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=[],
            dry_run=False,
        )
        == []
    )


def test_dump_data_sources_dumps_each_database():
    databases = [{'name': 'dc=example,dc=com'}, {'name': 'dc=other,dc=com'}]
    processes = [flexmock(), flexmock()]

    flexmock(module).should_receive('make_dump_path').and_return('/run/borgmatic')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/run/borgmatic/dump',
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        '/path/to/working/dir',
    )

    for database, process in zip(databases, processes):
        flexmock(module).should_receive('build_dump_command').with_args(
            database,
            '/run/borgmatic/dump',
        ).and_return(('slapcat', database['name'])).once()
        flexmock(module).should_receive('execute_command').with_args(
            ('slapcat', database['name']),
            run_to_completion=False,
            working_directory='/path/to/working/dir',
        ).and_return(process).once()

    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/run/borgmatic',
        'openldap_databases',
        [
            module.borgmatic.actions.restore.Dump('openldap_databases', 'dc=example,dc=com'),
            module.borgmatic.actions.restore.Dump('openldap_databases', 'dc=other,dc=com'),
        ],
    ).once()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').with_args(
        object,
        module.borgmatic.borg.pattern.Pattern(
            '/run/borgmatic/openldap_databases',
            source=module.borgmatic.borg.pattern.Pattern_source.HOOK,
        ),
    ).once()

    assert (
        module.dump_data_sources(
            databases,
            {},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=[],
            dry_run=False,
        )
        == processes
    )


def test_dump_data_sources_with_label_passes_it_through():
    databases = [{'name': 'dc=example,dc=com', 'label': 'ldap1'}]

    flexmock(module).should_receive('make_dump_path').and_return('/run/borgmatic')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').with_args(
        '/run/borgmatic',
        'dc=example,dc=com',
        label='ldap1',
    ).and_return('/run/borgmatic/dump').once()
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module.dump).should_receive('create_named_pipe_for_dump')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        None,
    )
    flexmock(module).should_receive('build_dump_command').and_return(('slapcat',))
    flexmock(module).should_receive('execute_command').and_return(flexmock())
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').with_args(
        '/run/borgmatic',
        'openldap_databases',
        [
            module.borgmatic.actions.restore.Dump(
                'openldap_databases', 'dc=example,dc=com', label='ldap1'
            ),
        ],
    ).once()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern')

    module.dump_data_sources(
        databases,
        {},
        config_paths=('test.yaml',),
        borgmatic_runtime_directory='/run/borgmatic',
        patterns=[],
        dry_run=False,
    )


def test_dump_data_sources_with_dry_run_skips_dump():
    databases = [{'name': 'dc=example,dc=com'}]

    flexmock(module).should_receive('make_dump_path').and_return('/run/borgmatic')
    flexmock(module.dump).should_receive('make_data_source_dump_filename').and_return(
        '/run/borgmatic/dump',
    )
    flexmock(module.os.path).should_receive('exists').and_return(False)
    flexmock(module).should_receive('build_dump_command').and_return(('slapcat',))
    flexmock(module.dump).should_receive('create_named_pipe_for_dump').never()
    flexmock(module).should_receive('execute_command').never()
    flexmock(module.dump).should_receive('write_data_source_dumps_metadata').never()
    flexmock(module.borgmatic.hooks.data_source.config).should_receive('inject_pattern').never()

    assert (
        module.dump_data_sources(
            databases,
            {},
            config_paths=('test.yaml',),
            borgmatic_runtime_directory='/run/borgmatic',
            patterns=[],
            dry_run=True,
        )
        == []
    )


def test_build_restore_command_selects_database_by_suffix():
    flexmock(module).should_receive('make_debug_flags').and_return(())

    assert module.build_restore_command({'name': 'dc=example,dc=com'}) == (
        'slapadd',
        '-b',
        'dc=example,dc=com',
    )


def test_build_restore_command_with_slapadd_command_uses_it():
    flexmock(module).should_receive('make_debug_flags').and_return(())

    assert module.build_restore_command(
        {'name': 'dc=example,dc=com', 'slapadd_command': '/usr/sbin/slapadd -q'},
    ) == ('/usr/sbin/slapadd', '-q', '-b', 'dc=example,dc=com')


def test_build_restore_command_passes_shell_metacharacters_through_literally():
    flexmock(module).should_receive('make_debug_flags').and_return(())

    assert module.build_restore_command(
        {'name': 'dc=example,dc=com', 'slapadd_command': 'slapadd *'},
    ) == ('slapadd', '*', '-b', 'dc=example,dc=com')


def test_build_restore_command_with_space_in_suffix_passes_it_through():
    flexmock(module).should_receive('make_debug_flags').and_return(())

    assert module.build_restore_command({'name': 'o=Example Corp,dc=example,dc=com'}) == (
        'slapadd',
        '-b',
        'o=Example Corp,dc=example,dc=com',
    )


def test_build_restore_command_includes_debug_flags():
    flexmock(module).should_receive('make_debug_flags').and_return(('-d', '256'))

    assert module.build_restore_command({'name': 'dc=example,dc=com'}) == (
        'slapadd',
        '-d',
        '256',
        '-b',
        'dc=example,dc=com',
    )


def test_restore_data_source_dump_restores_database():
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('build_restore_command').with_args(
        {'name': 'dc=example,dc=com'},
    ).and_return(('slapadd', '-b', 'dc=example,dc=com')).once()
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('slapadd', '-b', 'dc=example,dc=com'),
        [extract_process],
        output_log_level=module.logging.DEBUG,
        input_file=extract_process.stdout,
        working_directory=None,
        borg_local_path='borg',
    ).and_yield().once()

    module.restore_data_source_dump(
        hook_config=None,
        config={},
        data_source={'name': 'dc=example,dc=com'},
        dry_run=False,
        extract_process=extract_process,
        connection_params={},
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_with_local_path_uses_it_as_borg_local_path():
    extract_process = flexmock(stdout=flexmock())

    flexmock(module).should_receive('build_restore_command').and_return(
        ('slapadd', '-b', 'dc=example,dc=com'),
    )
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(None)
    flexmock(module).should_receive('execute_command_with_processes').with_args(
        ('slapadd', '-b', 'dc=example,dc=com'),
        [extract_process],
        output_log_level=module.logging.DEBUG,
        input_file=extract_process.stdout,
        working_directory=None,
        borg_local_path='borg1',
    ).and_yield().once()

    module.restore_data_source_dump(
        hook_config=None,
        config={'local_path': 'borg1'},
        data_source={'name': 'dc=example,dc=com'},
        dry_run=False,
        extract_process=extract_process,
        connection_params={},
        borgmatic_runtime_directory='/run/borgmatic',
    )


def test_restore_data_source_dump_with_dry_run_skips_restore():
    flexmock(module).should_receive('build_restore_command').and_return(('slapadd',))
    flexmock(module).should_receive('execute_command_with_processes').never()

    module.restore_data_source_dump(
        hook_config=None,
        config={},
        data_source={'name': 'dc=example,dc=com'},
        dry_run=True,
        extract_process=flexmock(),
        connection_params={},
        borgmatic_runtime_directory='/run/borgmatic',
    )
