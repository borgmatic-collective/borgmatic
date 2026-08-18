import pytest
from flexmock import flexmock

from borgmatic.actions.browse import workers as module


def test_add_repository_archives_publishes_for_each_archive():
    flexmock(module.borgmatic.actions.browse.archive).should_receive(
        'get_repository_archives'
    ).and_return({'archives': [{'archive': 'foo'}, {'archive': 'bar'}]})
    archive_loaded = flexmock()
    archive_loaded.should_receive('publish').with_args('bar').once()  # Reversed order.
    archive_loaded.should_receive('publish').with_args('foo').once()
    archive_loaded.should_receive('publish').with_args(module.LOADING_DONE).once()

    module.add_repository_archives.__wrapped__(
        browse_app=flexmock(),
        archive_loaded=archive_loaded,
        config=flexmock(),
        repository=flexmock(),
    )


def test_record_path_sets_file_path_in_filesystem_hierarchy():
    archive_path = flexmock(path_type='-', file_path='foo/bar/baz.txt')
    quux_path = flexmock()
    hierarchy = {'foo': {'bar': {'quux.txt': quux_path}, 'empty': {}}}

    module.record_path(
        archive_path=archive_path, hierarchy=hierarchy, path_components=('foo', 'bar', 'baz.txt')
    )

    assert hierarchy == {
        'foo': {'bar': {'quux.txt': quux_path, 'baz.txt': archive_path}, 'empty': {}}
    }


def test_record_path_sets_directory_path_in_filesystem_hierarchy():
    archive_path = flexmock(path_type='d', file_path='foo/bar/baz')
    quux_path = flexmock()
    hierarchy = {'foo': {'bar': {'quux.txt': quux_path}, 'empty': {}}}

    module.record_path(
        archive_path=archive_path, hierarchy=hierarchy, path_components=('foo', 'bar', 'baz')
    )

    assert hierarchy == {'foo': {'bar': {'quux.txt': quux_path, 'baz': {}}, 'empty': {}}}


def test_get_paths_lists_directory_contents():
    baz_path = module.borgmatic.actions.browse.archive.Archive_path('-', 'foo/bar/baz.txt', '')
    hierarchy = {'foo': {'bar': {'baz.txt': baz_path, 'other': {}}}, 'nope': {}}

    assert tuple(module.get_paths(hierarchy, ('foo', 'bar'))) == (
        baz_path,
        module.borgmatic.actions.browse.archive.Archive_path('d', 'foo/bar/other', ''),
    )


def test_get_paths_with_full_path_components_lists_directory_contents():
    baz_path = module.borgmatic.actions.browse.archive.Archive_path('-', 'etc/foo/bar/baz.txt', '')
    hierarchy = {'foo': {'bar': {'baz.txt': baz_path, 'other': {}}}, 'nope': {}}

    assert tuple(module.get_paths(hierarchy, ('foo', 'bar'), ('etc', 'foo', 'bar'))) == (
        baz_path,
        module.borgmatic.actions.browse.archive.Archive_path('d', 'etc/foo/bar/other', ''),
    )


def test_get_paths_lists_empty_directory_contents():
    baz_path = module.borgmatic.actions.browse.archive.Archive_path('-', 'etc/foo/bar/baz.txt', '')
    hierarchy = {'foo': {'bar': {'baz.txt': baz_path, 'other': {}}}, 'nope': {}}

    assert (
        tuple(module.get_paths(hierarchy, ('foo', 'bar', 'other'), ('etc', 'foo', 'bar', 'other')))
        == ()
    )


def test_get_paths_with_unknown_file_raises():
    hierarchy = {'foo': {'other': {}}}

    with pytest.raises(ValueError):
        tuple(module.get_paths(hierarchy, ('foo', 'bar.txt')))


def test_get_paths_with_unknown_directory_raises():
    hierarchy = {'foo': {'other': {}}}

    with pytest.raises(ValueError):
        tuple(module.get_paths(hierarchy, ('foo', 'bar', 'baz')))


def test_load_archive_paths_publishes_for_each_archive_path():
    flexmock(module.borgmatic.actions.browse.archive).should_receive('get_archive_paths').and_yield(
        'foo.txt', 'bar.txt'
    )
    path_loaded = flexmock()
    path_loaded.should_receive('publish').with_args('foo.txt').once()
    path_loaded.should_receive('publish').with_args('bar.txt').once()
    path_loaded.should_receive('publish').with_args(module.LOADING_DONE).once()

    module.load_archive_paths.__wrapped__(
        browse_app=flexmock(),
        path_loaded=path_loaded,
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
    )


def test_load_file_preview_publishes_file_contents():
    flexmock(module.borgmatic.actions.browse.archive).should_receive(
        'get_archive_file_content'
    ).and_return('hi')
    file_preview_loaded = flexmock()
    file_preview_loaded.should_receive('publish').with_args('hi').once()

    module.load_file_preview.__wrapped__(
        browse_app=flexmock(),
        file_preview_loaded=file_preview_loaded,
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        file_path='foo/bar/baz.txt',
    )
