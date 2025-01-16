from borgmatic.borg.pattern import Pattern
from borgmatic.hooks.data_source import snapshot as module


def test_get_contained_patterns_without_candidates_returns_empty():
    assert module.get_contained_patterns('/mnt', {}) == ()


def test_get_contained_patterns_with_self_candidate_returns_self():
    candidates = {Pattern('/foo'), Pattern('/mnt'), Pattern('/bar')}

    assert module.get_contained_patterns('/mnt', candidates) == (Pattern('/mnt'),)
    assert candidates == {Pattern('/foo'), Pattern('/bar')}


def test_get_contained_patterns_with_self_candidate_and_caret_prefix_returns_self():
    candidates = {Pattern('^/foo'), Pattern('^/mnt'), Pattern('^/bar')}

    assert module.get_contained_patterns('/mnt', candidates) == (Pattern('^/mnt'),)
    assert candidates == {Pattern('^/foo'), Pattern('^/bar')}


def test_get_contained_patterns_with_child_candidate_returns_child():
    candidates = {Pattern('/foo'), Pattern('/mnt/subdir'), Pattern('/bar')}

    assert module.get_contained_patterns('/mnt', candidates) == (Pattern('/mnt/subdir'),)
    assert candidates == {Pattern('/foo'), Pattern('/bar')}


def test_get_contained_patterns_with_grandchild_candidate_returns_child():
    candidates = {Pattern('/foo'), Pattern('/mnt/sub/dir'), Pattern('/bar')}

    assert module.get_contained_patterns('/mnt', candidates) == (Pattern('/mnt/sub/dir'),)
    assert candidates == {Pattern('/foo'), Pattern('/bar')}
