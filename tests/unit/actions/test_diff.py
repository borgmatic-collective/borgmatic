from flexmock import flexmock

from borgmatic.actions import diff as module


def test_run_diff_calls_borg_diff():
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive'
    ).and_return('archive2')
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.borg.diff).should_receive('diff').once()

    module.borgmatic.actions.diff.run_diff(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            archive='archive',
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive=None,
            only_patterns=False,
        ),
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )


def test_run_diff_with_only_patterns():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').once().and_return(
        []
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').once().and_return(
        []
    )
    flexmock(module.borgmatic.borg.repo_list).should_receive('resolve_archive_name').and_return(
        'archive'
    ).and_return('archive2')
    flexmock(module.borgmatic.borg.diff).should_receive('diff').once()

    module.borgmatic.actions.diff.run_diff(
        repository={'path': 'repo'},
        config={},
        local_borg_version=None,
        diff_arguments=flexmock(
            archive='archive',
            same_chunker_params=False,
            sort_keys=[],
            content_only=False,
            second_archive=None,
            only_patterns=True,
        ),
        global_arguments=flexmock(),
        local_path=None,
        remote_path=None,
    )
