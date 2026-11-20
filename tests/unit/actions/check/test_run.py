import pytest
from flexmock import flexmock

from borgmatic.actions.check import run as module
from borgmatic.borg.pattern import Pattern


def test_parse_checks_returns_them_as_tuple():
    checks = module.parse_checks({'checks': [{'name': 'foo'}, {'name': 'bar'}]})

    assert checks == ('foo', 'bar')


def test_parse_checks_with_missing_value_returns_defaults():
    checks = module.parse_checks({})

    assert checks == ('repository', 'archives')


def test_parse_checks_with_empty_list_returns_defaults():
    checks = module.parse_checks({'checks': []})

    assert checks == ('repository', 'archives')


def test_parse_checks_with_none_value_returns_defaults():
    checks = module.parse_checks({'checks': None})

    assert checks == ('repository', 'archives')


def test_parse_checks_with_disabled_returns_no_checks():
    checks = module.parse_checks({'checks': [{'name': 'foo'}, {'name': 'disabled'}]})

    assert checks == ()


def test_parse_checks_prefers_override_checks_to_configured_checks():
    checks = module.parse_checks(
        {'checks': [{'name': 'archives'}]},
        only_checks=['repository', 'extract'],
    )

    assert checks == ('repository', 'extract')


def test_run_check_checks_archives_for_configured_repository():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module.borgmatic.actions.check.frequency).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module.borgmatic.actions.check.frequency).should_receive('filter_checks_on_frequency').and_return(
        {'repository', 'archives'},
    )
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').once()
    flexmock(module.borgmatic.actions.check.frequency).should_receive('make_check_time_path')
    flexmock(module.borgmatic.actions.check.frequency).should_receive('write_check_time')
    flexmock(module.borgmatic.borg.extract).should_receive('extract_last_archive_dry_run').never()
    check_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        repair=False,
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_with_repair_skips_check_times():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module.borgmatic.actions.check.frequency).should_receive('upgrade_check_times').never()
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module.borgmatic.actions.check.frequency).should_receive('filter_checks_on_frequency').and_return(
        {'repository', 'archives'},
    )
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').once()
    flexmock(module.borgmatic.actions.check.frequency).should_receive('make_check_time_path')
    flexmock(module.borgmatic.actions.check.frequency).should_receive('write_check_time').never()
    flexmock(module.borgmatic.borg.extract).should_receive('extract_last_archive_dry_run').never()
    check_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        repair=True,
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_runs_configured_extract_check():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module.borgmatic.actions.check.frequency).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module.borgmatic.actions.check.frequency).should_receive('filter_checks_on_frequency').and_return({'extract'})
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').never()
    flexmock(module.borgmatic.borg.extract).should_receive('extract_last_archive_dry_run').once()
    flexmock(module.borgmatic.actions.check.frequency).should_receive('make_check_time_path')
    flexmock(module.borgmatic.actions.check.frequency).should_receive('write_check_time')
    check_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        repair=False,
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_runs_configured_spot_check():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module.borgmatic.actions.check.frequency).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module.borgmatic.actions.check.frequency).should_receive('filter_checks_on_frequency').and_return({'spot'})
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').never()
    flexmock(module.borgmatic.config.paths).should_receive('Runtime_directory').and_return(
        flexmock(),
    )
    flexmock(module.borgmatic.actions.check.spot).should_receive('spot_check').once()
    flexmock(module.borgmatic.actions.check.frequency).should_receive('make_check_time_path')
    flexmock(module.borgmatic.actions.check.frequency).should_receive('write_check_time')
    check_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        repair=False,
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )


def test_run_check_without_checks_runs_nothing_except_hooks():
    flexmock(module.logger).answer = lambda message: None
    flexmock(module.borgmatic.borg.check).should_receive('get_repository_id').and_return(flexmock())
    flexmock(module.borgmatic.actions.check.frequency).should_receive('upgrade_check_times')
    flexmock(module).should_receive('parse_checks')
    flexmock(module.borgmatic.borg.check).should_receive('make_archive_filter_flags').and_return(())
    flexmock(module).should_receive('make_archives_check_id').and_return(None)
    flexmock(module.borgmatic.actions.check.frequency).should_receive('filter_checks_on_frequency').and_return({})
    flexmock(module.borgmatic.borg.check).should_receive('check_archives').never()
    flexmock(module.borgmatic.actions.check.frequency).should_receive('make_check_time_path')
    flexmock(module.borgmatic.actions.check.frequency).should_receive('write_check_time').never()
    flexmock(module.borgmatic.borg.extract).should_receive('extract_last_archive_dry_run').never()
    check_arguments = flexmock(
        repository=None,
        progress=flexmock(),
        repair=False,
        only_checks=flexmock(),
        force=flexmock(),
    )
    global_arguments = flexmock(monitoring_verbosity=1, dry_run=False)

    module.run_check(
        config_filename='test.yaml',
        repository={'path': 'repo'},
        config={'repositories': ['repo']},
        local_borg_version=None,
        check_arguments=check_arguments,
        global_arguments=global_arguments,
        local_path=None,
        remote_path=None,
    )
