from flexmock import flexmock

from borgmatic.actions.browse import directory_list as module


def test_get_relative_archive_path_components_strips_off_current_directory():
    assert module.get_relative_archive_path_components(
        flexmock(file_path='foo/bar/baz/quux.txt'), ('foo', 'bar')
    ) == ('baz', 'quux.txt')


def test_get_relative_archive_path_components_with_root_current_directory_strips_off_nothing():
    assert module.get_relative_archive_path_components(
        flexmock(file_path='foo/bar/baz/quux.txt'), ()
    ) == ('foo', 'bar', 'baz', 'quux.txt')


def test_get_relative_archive_path_components_with_non_matching_paths_returns_none():
    assert (
        module.get_relative_archive_path_components(
            flexmock(file_path='foo/bar/baz/quux.txt'), ('etc',)
        )
        is None
    )


def test_make_directory_list_option_with_file_path_makes_file_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='-', file_path='foo/bar/baz.txt', link_target=''), ('baz.txt',)
    )

    assert option.prompt == '📄 baz.txt'
    assert option.id == 'baz.txt'


def test_make_directory_list_option_with_directory_path_makes_directory_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='d', file_path='foo/bar/baz', link_target=''), ('baz',)
    )

    assert option.prompt == '📁 baz'
    assert option.id == 'baz'


def test_make_directory_list_option_with_contained_file_path_makes_directory_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='d', file_path='foo/bar/baz.txt', link_target=''),
        (
            'bar',
            'baz.txt',
        ),
    )

    assert option.prompt == '📁 bar'
    assert option.id == 'bar'


def test_make_directory_list_option_with_link_path_makes_link_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='l', file_path='foo/bar/baz.txt', link_target='quux.txt'), ('baz.txt',)
    )

    assert option.prompt == '🔗 baz.txt → quux.txt'
    assert option.id == 'baz.txt'


def test_make_directory_list_option_with_pipe_path_makes_pipe_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='p', file_path='foo/bar/baz.txt', link_target=''), ('baz.txt',)
    )

    assert option.prompt == '🚰 baz.txt'
    assert option.id == 'baz.txt'


def test_make_directory_list_option_with_unknown_path_makes_unknown_option():
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='wtf', file_path='foo/bar/baz.txt', link_target=''), ('baz.txt',)
    )

    assert option.prompt == '❓ baz.txt'
    assert option.id == 'baz.txt'
