import pytest

from borgmatic.actions.check import paths as module


@pytest.mark.parametrize(
    'source_path,expected_result',
    (
        ('/base/foo/bar/a', 'bar/a'),
        ('/base/other', 'base/other'),
    ),
)
def test_map_source_path_to_archive_path_replaces_source_root_with_archive_root(
    source_path, expected_result
):
    source_to_archive_root_paths = module.make_source_to_archive_root_map(
        (module.borgmatic.borg.pattern.Pattern('/base/foo/./bar'),)
    )
    archive_paths = {'bar/a', 'top', 'base/other'}

    assert (
        module.map_source_path_to_archive_path(
            source_path, archive_paths, source_to_archive_root_paths
        )
        == expected_result
    )
