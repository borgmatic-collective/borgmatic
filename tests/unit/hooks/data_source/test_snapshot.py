from borgmatic.hooks.data_source import snapshot as module


def test_get_contained_directories_without_candidates_returns_empty():
    assert module.get_contained_directories('/mnt', {}) == ()


def test_get_contained_directories_with_self_candidate_returns_self():
    candidates = {'/foo', '/mnt', '/bar'}

    assert module.get_contained_directories('/mnt', candidates) == ('/mnt',)
    assert candidates == {'/foo', '/bar'}


def test_get_contained_directories_with_child_candidate_returns_child():
    candidates = {'/foo', '/mnt/subdir', '/bar'}

    assert module.get_contained_directories('/mnt', candidates) == ('/mnt/subdir',)
    assert candidates == {'/foo', '/bar'}


def test_get_contained_directories_with_grandchild_candidate_returns_child():
    candidates = {'/foo', '/mnt/sub/dir', '/bar'}

    assert module.get_contained_directories('/mnt', candidates) == ('/mnt/sub/dir',)
    assert candidates == {'/foo', '/bar'}
