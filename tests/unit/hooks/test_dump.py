import pytest
from flexmock import flexmock

from borgmatic.hooks import dump as module


def test_make_database_dump_filename_uses_name_and_hostname():
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')

    assert (
        module.make_database_dump_filename('databases', 'test', 'hostname')
        == 'databases/hostname/test'
    )


def test_make_database_dump_filename_without_hostname_defaults_to_localhost():
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')

    assert module.make_database_dump_filename('databases', 'test') == 'databases/localhost/test'


def test_make_database_dump_filename_with_invalid_name_raises():
    flexmock(module.os.path).should_receive('expanduser').and_return('databases')

    with pytest.raises(ValueError):
        module.make_database_dump_filename('databases', 'invalid/name')


def test_flatten_dump_patterns_produces_list_of_all_patterns():
    dump_patterns = {'postgresql_databases': ['*/glob', 'glob/*'], 'mysql_databases': ['*/*/*']}
    expected_patterns = sorted(
        dump_patterns['postgresql_databases'] + dump_patterns['mysql_databases']
    )

    assert sorted(module.flatten_dump_patterns(dump_patterns, ('bob',))) == expected_patterns


def test_flatten_dump_patterns_with_no_patterns_errors():
    dump_patterns = {'postgresql_databases': [], 'mysql_databases': []}

    with pytest.raises(ValueError):
        assert module.flatten_dump_patterns(dump_patterns, ('bob',))


def test_flatten_dump_patterns_with_no_hooks_errors():
    dump_patterns = {}

    with pytest.raises(ValueError):
        assert module.flatten_dump_patterns(dump_patterns, ('bob',))


def test_remove_database_dumps_removes_dump_for_each_database():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module).should_receive('make_database_dump_filename').with_args(
        'databases', 'foo', None
    ).and_return('databases/localhost/foo')
    flexmock(module).should_receive('make_database_dump_filename').with_args(
        'databases', 'bar', None
    ).and_return('databases/localhost/bar')

    flexmock(module.os).should_receive('remove').with_args('databases/localhost/foo').once()
    flexmock(module.os).should_receive('remove').with_args('databases/localhost/bar').once()
    flexmock(module.os).should_receive('listdir').with_args('databases/localhost').and_return(
        ['bar']
    ).and_return([])

    flexmock(module.os).should_receive('rmdir').with_args('databases/localhost').once()

    module.remove_database_dumps('databases', databases, 'SuperDB', 'test.yaml', dry_run=False)


def test_remove_database_dumps_with_dry_run_skips_removal():
    databases = [{'name': 'foo'}, {'name': 'bar'}]
    flexmock(module.os).should_receive('rmdir').never()
    flexmock(module.os).should_receive('remove').never()

    module.remove_database_dumps('databases', databases, 'SuperDB', 'test.yaml', dry_run=True)


def test_remove_database_dumps_without_databases_does_not_raise():
    module.remove_database_dumps('databases', [], 'SuperDB', 'test.yaml', dry_run=False)


def test_convert_glob_patterns_to_borg_patterns_removes_leading_slash():
    assert module.convert_glob_patterns_to_borg_patterns(('/etc/foo/bar',)) == ['sh:etc/foo/bar']


def test_get_database_names_from_dumps_gets_names_from_filenames_matching_globs():
    flexmock(module.glob).should_receive('glob').and_return(
        ('databases/localhost/foo',)
    ).and_return(('databases/localhost/bar',)).and_return(())

    assert module.get_database_names_from_dumps(
        ('databases/*/foo', 'databases/*/bar', 'databases/*/baz')
    ) == ['foo', 'bar']


def test_get_database_configurations_only_produces_named_databases():
    databases = [
        {'name': 'foo', 'hostname': 'example.org'},
        {'name': 'bar', 'hostname': 'example.com'},
        {'name': 'baz', 'hostname': 'example.org'},
    ]

    assert list(module.get_database_configurations(databases, ('foo', 'baz'))) == [
        {'name': 'foo', 'hostname': 'example.org'},
        {'name': 'baz', 'hostname': 'example.org'},
    ]


def test_get_database_configurations_matches_all_database():
    databases = [
        {'name': 'foo', 'hostname': 'example.org'},
        {'name': 'all', 'hostname': 'example.com'},
    ]

    assert list(module.get_database_configurations(databases, ('foo', 'bar', 'baz'))) == [
        {'name': 'foo', 'hostname': 'example.org'},
        {'name': 'bar', 'hostname': 'example.com'},
        {'name': 'baz', 'hostname': 'example.com'},
    ]


def test_get_per_hook_database_configurations_partitions_by_hook():
    hooks = {'postgresql_databases': [flexmock()]}
    names = ('foo', 'bar')
    dump_patterns = flexmock()
    expected_config = {'postgresql_databases': [{'name': 'foo'}, {'name': 'bar'}]}
    flexmock(module).should_receive('get_database_configurations').with_args(
        hooks['postgresql_databases'], names
    ).and_return(expected_config['postgresql_databases'])

    config = module.get_per_hook_database_configurations(hooks, names, dump_patterns)

    assert config == expected_config


def test_get_per_hook_database_configurations_defaults_to_detected_database_names():
    hooks = {'postgresql_databases': [flexmock()]}
    names = ()
    detected_names = flexmock()
    dump_patterns = {'postgresql_databases': [flexmock()]}
    expected_config = {'postgresql_databases': [flexmock()]}
    flexmock(module).should_receive('get_database_names_from_dumps').and_return(detected_names)
    flexmock(module).should_receive('get_database_configurations').with_args(
        hooks['postgresql_databases'], detected_names
    ).and_return(expected_config['postgresql_databases'])

    config = module.get_per_hook_database_configurations(hooks, names, dump_patterns)

    assert config == expected_config


def test_get_per_hook_database_configurations_with_unknown_database_name_raises():
    hooks = {'postgresql_databases': [flexmock()]}
    names = ('foo', 'bar')
    dump_patterns = flexmock()
    flexmock(module).should_receive('get_database_configurations').with_args(
        hooks['postgresql_databases'], names
    ).and_return([])

    with pytest.raises(ValueError):
        module.get_per_hook_database_configurations(hooks, names, dump_patterns)


def test_get_per_hook_database_configurations_with_all_and_no_archive_dumps_raises():
    hooks = {'postgresql_databases': [flexmock()]}
    names = ('foo', 'all')
    dump_patterns = flexmock()
    flexmock(module).should_receive('get_database_configurations').with_args(
        hooks['postgresql_databases'], names
    ).and_return([])

    with pytest.raises(ValueError):
        module.get_per_hook_database_configurations(hooks, names, dump_patterns)
