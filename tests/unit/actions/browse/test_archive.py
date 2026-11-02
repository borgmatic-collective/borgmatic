from flexmock import flexmock

from borgmatic.actions.browse import archive as module


def test_get_repository_archives_does_not_raise():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.borg.version).should_receive('local_borg_version').and_return('3.0')
    flexmock(module.borgmatic.borg.repo_list).should_receive('list_repository').and_return('{}')

    assert module.get_repository_archives(config, config['repositories'][0]) == {}


def test_get_archive_paths_returns_each_as_archive_path_with_metadata():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.borg.version).should_receive('local_borg_version').and_return('3.0')
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').with_args(
        'test.borg',
        'archive',
        object,
        '3.0',
        object,
        path_format=object,
        local_path=object,
        remote_path=object,
    ).and_yield(
        {'path': 'foo.txt', 'type': '-', 'linktarget': '', 'size': 3},
        {'path': 'bar.txt', 'type': 'l', 'linktarget': 'foo.txt', 'size': 0},
        {'path': 'etc', 'type': 'd', 'linktarget': '', 'size': 0},
    )

    assert tuple(
        module.get_archive_paths(config, config['repositories'][0], 'b33f', 'archive')
    ) == (
        module.Archive_path('-', 'foo.txt', '', 3),
        module.Archive_path('l', 'bar.txt', 'foo.txt', 0),
        module.Archive_path('d', 'etc', '', 0),
    )


def test_get_archive_paths_defaults_missing_size_to_zero():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.borg.version).should_receive('local_borg_version').and_return('3.0')
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').and_yield(
        {'path': 'foo.txt', 'type': '-', 'linktarget': ''},
    )

    assert tuple(
        module.get_archive_paths(config, config['repositories'][0], 'b33f', 'archive')
    ) == (module.Archive_path('-', 'foo.txt', '', 0),)


def test_get_archive_paths_with_feature_available_uses_archive_id_instead_of_name():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.borg.version).should_receive('local_borg_version').and_return('3.0')
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.list).should_receive('capture_archive_listing').with_args(
        'test.borg',
        'aid:b33f',
        object,
        '3.0',
        object,
        path_format=object,
        local_path=object,
        remote_path=object,
    ).and_yield(
        {'path': 'foo.txt', 'type': '-', 'linktarget': '', 'size': 3},
        {'path': 'bar.txt', 'type': 'l', 'linktarget': 'foo.txt', 'size': 0},
        {'path': 'etc', 'type': 'd', 'linktarget': '', 'size': 0},
    )

    assert tuple(
        module.get_archive_paths(config, config['repositories'][0], 'b33f', 'archive')
    ) == (
        module.Archive_path('-', 'foo.txt', '', 3),
        module.Archive_path('l', 'bar.txt', 'foo.txt', 0),
        module.Archive_path('d', 'etc', '', 0),
    )


def test_get_archive_file_content_with_binary_file_bails():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.borg.version).should_receive('local_borg_version').and_return('3.0')
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process := flexmock()
    )
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.execute).should_receive('log_outputs').and_return(
        (b'foo\n', b'bar\n')
    )
    extract_process.should_receive('terminate').never()
    flexmock(module.binaryornot.helpers).should_receive('is_binary_string').and_return(True)

    assert (
        module.get_archive_file_content(
            config, config['repositories'][0], 'b33f', 'archive', 'etc/foo.txt'
        )
        is None
    )


def test_get_archive_file_content_decodes_content():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.borg.version).should_receive('local_borg_version').and_return('3.0')
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').with_args(
        dry_run=False,
        repository='test.borg',
        archive='archive',
        paths=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        destination_path=None,
        strip_components=None,
        extract_to_stdout=True,
    ).and_return(extract_process := flexmock())
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.execute).should_receive('log_outputs').and_return(
        (b'foo\n', b'bar\n')
    )
    extract_process.should_receive('terminate').never()
    flexmock(module.binaryornot.helpers).should_receive('is_binary_string').and_return(False)

    assert (
        module.get_archive_file_content(
            config, config['repositories'][0], 'b33f', 'archive', 'etc/foo.txt'
        )
        == 'foo\nbar\n'
    )


def test_get_archive_file_content_with_large_file_truncates_content():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.borg.version).should_receive('local_borg_version').and_return('3.0')
    flexmock(module, MAXIMUM_TOTAL_READ_SIZE=3)
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process := flexmock()
    )
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.execute).should_receive('log_outputs').and_return(
        (b'foo\n', b'bar\n')
    )
    extract_process.should_receive('terminate').once()
    flexmock(module.binaryornot.helpers).should_receive('is_binary_string').and_return(False)

    assert (
        module.get_archive_file_content(
            config, config['repositories'][0], 'b33f', 'archive', 'etc/foo.txt'
        )
        == f'foo\nbar\n\n{module.TRUNCATION_MESSAGE}'
    )


def test_get_archive_file_content_with_unicode_decode_error_does_not_raise():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.borg.version).should_receive('local_borg_version').and_return('3.0')
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(False)
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').and_return(
        extract_process := flexmock()
    )
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.execute).should_receive('log_outputs').and_return(
        (b'foo\n', b'\xc3\n')
    )
    extract_process.should_receive('terminate').never()
    flexmock(module.binaryornot.helpers).should_receive('is_binary_string').and_return(False)

    assert (
        module.get_archive_file_content(
            config, config['repositories'][0], 'b33f', 'archive', 'etc/foo.txt'
        )
        is None
    )


def test_get_archive_file_content_with_feature_available_uses_archive_id_instead_of_name():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.borg.version).should_receive('local_borg_version').and_return('3.0')
    flexmock(module.borgmatic.borg.feature).should_receive('available').and_return(True)
    flexmock(module.borgmatic.borg.extract).should_receive('extract_archive').with_args(
        dry_run=False,
        repository='test.borg',
        archive='aid:b33f',
        paths=object,
        config=object,
        local_borg_version=object,
        global_arguments=object,
        local_path=object,
        remote_path=object,
        destination_path=None,
        strip_components=None,
        extract_to_stdout=True,
    ).and_return(extract_process := flexmock())
    flexmock(module.borgmatic.logger).should_receive('Log_prefix').and_return(flexmock())
    flexmock(module.borgmatic.execute).should_receive('log_outputs').and_return(
        (b'foo\n', b'bar\n')
    )
    extract_process.should_receive('terminate').never()
    flexmock(module.binaryornot.helpers).should_receive('is_binary_string').and_return(False)

    assert (
        module.get_archive_file_content(
            config, config['repositories'][0], 'b33f', 'archive', 'etc/foo.txt'
        )
        == 'foo\nbar\n'
    )
