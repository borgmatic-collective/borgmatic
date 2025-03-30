from flexmock import flexmock

from borgmatic.borg.pattern import Pattern
from borgmatic.hooks.data_source import snapshot as module


def test_get_contained_patterns_without_candidates_returns_empty():
    flexmock(module.os).should_receive('stat').and_return(flexmock(st_dev=flexmock()))

    assert module.get_contained_patterns('/mnt', {}) == ()


def test_get_contained_patterns_with_self_candidate_returns_self():
    device = flexmock()
    flexmock(module.os).should_receive('stat').and_return(flexmock(st_dev=device))
    candidates = {
        Pattern('/foo', device=device),
        Pattern('/mnt', device=device),
        Pattern('/bar', device=device),
    }

    assert module.get_contained_patterns('/mnt', candidates) == (Pattern('/mnt', device=device),)
    assert candidates == {Pattern('/foo', device=device), Pattern('/bar', device=device)}


def test_get_contained_patterns_with_self_candidate_and_caret_prefix_returns_self():
    device = flexmock()
    flexmock(module.os).should_receive('stat').and_return(flexmock(st_dev=device))
    candidates = {
        Pattern('^/foo', device=device),
        Pattern('^/mnt', device=device),
        Pattern('^/bar', device=device),
    }

    assert module.get_contained_patterns('/mnt', candidates) == (Pattern('^/mnt', device=device),)
    assert candidates == {Pattern('^/foo', device=device), Pattern('^/bar', device=device)}


def test_get_contained_patterns_with_child_candidate_returns_child():
    device = flexmock()
    flexmock(module.os).should_receive('stat').and_return(flexmock(st_dev=device))
    candidates = {
        Pattern('/foo', device=device),
        Pattern('/mnt/subdir', device=device),
        Pattern('/bar', device=device),
    }

    assert module.get_contained_patterns('/mnt', candidates) == (
        Pattern('/mnt/subdir', device=device),
    )
    assert candidates == {Pattern('/foo', device=device), Pattern('/bar', device=device)}


def test_get_contained_patterns_with_grandchild_candidate_returns_child():
    device = flexmock()
    flexmock(module.os).should_receive('stat').and_return(flexmock(st_dev=device))
    candidates = {
        Pattern('/foo', device=device),
        Pattern('/mnt/sub/dir', device=device),
        Pattern('/bar', device=device),
    }

    assert module.get_contained_patterns('/mnt', candidates) == (
        Pattern('/mnt/sub/dir', device=device),
    )
    assert candidates == {Pattern('/foo', device=device), Pattern('/bar', device=device)}


def test_get_contained_patterns_ignores_child_candidate_on_another_device():
    one_device = flexmock()
    another_device = flexmock()
    flexmock(module.os).should_receive('stat').and_return(flexmock(st_dev=one_device))
    candidates = {
        Pattern('/foo', device=one_device),
        Pattern('/mnt/subdir', device=another_device),
        Pattern('/bar', device=one_device),
    }

    assert module.get_contained_patterns('/mnt', candidates) == ()
    assert candidates == {
        Pattern('/foo', device=one_device),
        Pattern('/mnt/subdir', device=another_device),
        Pattern('/bar', device=one_device),
    }
