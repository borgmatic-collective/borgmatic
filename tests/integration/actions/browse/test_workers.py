from flexmock import flexmock

from borgmatic.actions.browse import workers as module


def test_archive_path_loaded_publish_records_complete():
    signal = module.Archive_path_loaded(owner=flexmock(), name='Bob')
    signal.publish(module.LOADING_DONE)

    assert signal.complete


def test_archive_path_loaded_publish_records_published_path():
    archive_path = module.borgmatic.actions.browse.archive.Archive_path('-', 'foo/bar.txt', '')
    signal = module.Archive_path_loaded(owner=flexmock(), name='Bob')
    signal.publish(archive_path)

    assert signal.path_hierarchy == {'foo': {'bar.txt': archive_path}}
    assert not signal.complete
