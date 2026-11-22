import pytest
from flexmock import flexmock

from borgmatic.actions.check import paths as module


def test_collect_and_process_patterns_collects_archive_and_bootstrap_patterns():
    flexmock(module.borgmatic.config.paths).should_receive('get_working_directory').and_return(
        flexmock()
    )
    flexmock(module.borgmatic.actions.config.bootstrap).should_receive(
        'load_config_paths_from_archive'
    ).and_return(['test.yaml', 'other.yaml'])
    flexmock(module.borgmatic.actions.pattern).should_receive('collect_patterns').and_return(
        (module.borgmatic.borg.pattern.Pattern('/foo'),)
    )
    flexmock(module.borgmatic.actions.pattern).should_receive('process_patterns').replace_with(
        lambda patterns, *other: patterns
    )

    assert module.collect_and_process_patterns(
        repository={'path': 'test.borg'},
        archive=flexmock(),
        config=flexmock(),
        local_borg_version=flexmock(),
        global_arguments=flexmock(),
        borgmatic_runtime_directory=flexmock(),
    ) == (
        module.borgmatic.borg.pattern.Pattern('/foo'),
        module.borgmatic.borg.pattern.Pattern(
            'test.yaml',
            source=module.borgmatic.borg.pattern.Pattern_source.INTERNAL,
        ),
        module.borgmatic.borg.pattern.Pattern(
            'other.yaml',
            source=module.borgmatic.borg.pattern.Pattern_source.INTERNAL,
        ),
    )


@pytest.mark.parametrize(
    'path,expected_result',
    (
        ('foo/bar', 'foo/bar'),
        ('/foo/bar', 'foo/bar'),
        ('//foo/bar', 'foo/bar'),
        ('../foo/bar', 'foo/bar'),
        ('../../foo/bar', 'foo/bar'),
        ('/../../foo/bar', 'foo/bar'),
        ('/foo/../bar', 'foo/../bar'),
        ('../..', '.'),
        ('/', '.'),
        ('//', '.'),
        ('', '.'),
    ),
)
def test_make_borg_archive_path_strips_leading_slashes_and_dot_dots(path, expected_result):
    assert module.make_borg_archive_path(path) == expected_result


@pytest.mark.parametrize(
    'pattern_path,expected_pairs',
    (
        ('/foo/bar', (('/foo/bar', 'foo/bar'),)),
        ('/./foo/bar', (('/foo/bar', 'foo/bar'),)),
        ('/foo/./bar', (('/foo/bar', 'bar'),)),
        ('/foo/./bar/..', (('/foo', '.'),)),
        ('/foo/./..', (('/foo', '.'), ('/', '.'))),
        ('/tmp/base/foo/./..', (('/tmp/base/foo', '.'), ('/tmp/base', 'tmp/base'))),
    ),
)
def test_make_source_to_archive_root_map_produces_normalized_source_root_and_borg_equivalent(
    pattern_path, expected_pairs
):
    flexmock(module).should_receive('make_borg_archive_path').replace_with(
        lambda path: path.lstrip('/')
    )

    assert (
        module.make_source_to_archive_root_map(
            (module.borgmatic.borg.pattern.Pattern(pattern_path),)
        )
        == expected_pairs
    )


def test_make_source_to_archive_root_map_skips_non_root_pattern():
    flexmock(module).should_receive('make_borg_archive_path').never()

    assert (
        module.make_source_to_archive_root_map(
            (
                module.borgmatic.borg.pattern.Pattern(
                    '/foo',
                    type=module.borgmatic.borg.pattern.Pattern_type.INCLUDE,
                ),
            )
        )
        == ()
    )


def test_make_source_to_archive_root_map_sorts_results_by_longest_source_path():
    flexmock(module).should_receive('make_borg_archive_path').replace_with(
        lambda path: path.lstrip('/')
    )

    assert module.make_source_to_archive_root_map(
        (
            module.borgmatic.borg.pattern.Pattern('/bar/baz'),
            module.borgmatic.borg.pattern.Pattern('/bar/baz/./quux'),
        )
    ) == (
        ('/bar/baz/quux', 'quux'),
        ('/bar/baz', 'bar/baz'),
    )


@pytest.mark.parametrize(
    'source_path,source_root_path,archive_root_path,expected_result',
    (
        ('/foo/bar', '/foo', 'foo', 'foo/bar'),
        ('/foo', '/foo', 'foo', 'foo'),
        ('/foo', '/foo', '.', '.'),
    ),
)
def test_replace_root_path_prefix_swaps_source_root_for_archive_root(
    source_path, source_root_path, archive_root_path, expected_result
):
    flexmock(module).should_receive('make_borg_archive_path').replace_with(
        lambda path: path.lstrip('/')
    )

    assert (
        module.replace_root_path_prefix(source_path, source_root_path, archive_root_path)
        == expected_result
    )


@pytest.mark.parametrize(
    'source_path,archive_paths,source_to_archive_root_paths,expected_result',
    (
        ('/foo/bar', ('foo', 'baz'), (('/foo', 'foo'), ('/baz', 'baz')), 'foo/bar'),
        ('/foo/bar', ('not', 'matching'), (('/foo', 'foo'), ('/baz', 'baz')), 'foo/bar'),
        ('/foo', ('foo', 'baz'), (('/foo', 'foo'), ('/baz', 'baz')), 'foo'),
        (
            '/foo/bar/baz.txt',
            ('foo/bar/baz.txt',),
            (('/foo/bar', 'foo/bar'), ('/foo', '.')),
            'foo/bar/baz.txt',
        ),
        (
            '/foo/bar/baz.txt',
            ('.',),
            (('/foo/bar', 'foo/bar'), ('/foo', '.')),
            'foo/bar/baz.txt',
        ),
        ('/foo/bar', ('foo', 'baz'), (('/hmm', 'hmm'),), 'foo/bar'),
    ),
)
def test_map_source_path_to_archive_path_replaces_source_root_with_archive_root(
    source_path, archive_paths, source_to_archive_root_paths, expected_result
):
    flexmock(module).should_receive('replace_root_path_prefix').replace_with(
        lambda source_path, source_root_path, archive_root_path: source_path.replace(
            source_root_path, archive_root_path
        )
    )

    assert (
        module.map_source_path_to_archive_path(
            source_path, archive_paths, source_to_archive_root_paths
        )
        == expected_result
    )
