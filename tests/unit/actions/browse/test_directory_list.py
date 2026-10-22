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


def test_make_size_path_prompt_with_bytes_size_pads_unit():
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').with_args(
        358
    ).and_return('358 B')
    flexmock(module.rich.text).should_receive('Text').replace_with(lambda text: text)

    assert module.make_size_path_prompt(358, 'path') == '    358 B   path'


def test_make_size_path_prompt_with_larger_size_does_not_pad_unit():
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').with_args(
        1024
    ).and_return('1.02 kB')
    flexmock(module.rich.text).should_receive('Text').replace_with(lambda text: text)

    assert module.make_size_path_prompt(1024, 'path') == '   1.02 kB  path'


def test_make_size_path_prompt_with_no_size_leaves_size_column_blank():
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').never()
    flexmock(module.rich.text).should_receive('Text').replace_with(lambda text: text)

    assert module.make_size_path_prompt(None, 'path') == '            path'


def test_make_directory_list_option_with_file_path_makes_file_option():
    prompt = flexmock()
    flexmock(module).should_receive('make_size_path_prompt').with_args(
        1024, '📄 baz.txt'
    ).and_return(prompt)
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').with_args(
        1024
    ).and_return('1.02 kB')
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='-', file_path='foo/bar/baz.txt', link_target=''), ('baz.txt',), 1024
    )

    assert option.prompt == prompt
    assert option.prompt_text == '📄 baz.txt (1.02 kB)'
    assert option.path_type == '-'
    assert option.id == 'baz.txt'


def test_make_directory_list_option_with_directory_path_makes_directory_option():
    prompt = flexmock()
    flexmock(module).should_receive('make_size_path_prompt').with_args(2048, '📁 baz').and_return(
        prompt
    )
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').with_args(
        2048
    ).and_return('2.05 kB')
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='d', file_path='foo/bar/baz', link_target=''), ('baz',), 2048
    )

    assert option.prompt == prompt
    assert option.prompt_text == '📁 baz (2.05 kB)'
    assert option.path_type == 'd'
    assert option.id == 'baz'


def test_make_directory_list_option_with_contained_file_path_makes_directory_option():
    prompt = flexmock()
    flexmock(module).should_receive('make_size_path_prompt').with_args(0, '📁 bar').and_return(
        prompt
    )
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').with_args(
        0
    ).and_return('0 B')
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='d', file_path='foo/bar/baz.txt', link_target=''),
        (
            'bar',
            'baz.txt',
        ),
        0,
    )

    assert option.prompt == prompt
    assert option.prompt_text == '📁 bar (0 B)'
    assert option.path_type == 'd'
    assert option.id == 'bar'


def test_make_directory_list_option_with_contained_symlink_path_has_no_link_target():
    prompt = flexmock()
    flexmock(module).should_receive('make_size_path_prompt').with_args(0, '📁 mnt').and_return(
        prompt
    )
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').with_args(
        0
    ).and_return('0 B')
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='l', file_path='mnt/link', link_target='/home/foo/.git'),
        (
            'mnt',
            'link',
        ),
        0,
    )

    assert option.prompt == prompt
    assert option.prompt_text == '📁 mnt (0 B)'
    assert option.path_type == 'd'
    assert option.id == 'mnt'


def test_make_directory_list_option_with_link_path_makes_link_option():
    prompt = flexmock()
    flexmock(module).should_receive('make_size_path_prompt').with_args(
        0, '🔗 baz.txt → quux.txt'
    ).and_return(prompt)
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').with_args(
        0
    ).and_return('0 B')
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='l', file_path='foo/bar/baz.txt', link_target='quux.txt'),
        ('baz.txt',),
        0,
    )

    assert option.prompt == prompt
    assert option.prompt_text == '🔗 baz.txt → quux.txt (0 B)'
    assert option.path_type == 'l'
    assert option.id == 'baz.txt'


def test_make_directory_list_option_with_pipe_path_makes_pipe_option():
    prompt = flexmock()
    flexmock(module).should_receive('make_size_path_prompt').with_args(0, '🚰 baz.txt').and_return(
        prompt
    )
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').with_args(
        0
    ).and_return('0 B')
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='p', file_path='foo/bar/baz.txt', link_target=''), ('baz.txt',), 0
    )

    assert option.prompt == prompt
    assert option.prompt_text == '🚰 baz.txt (0 B)'
    assert option.path_type == 'p'
    assert option.id == 'baz.txt'


def test_make_directory_list_option_with_unknown_path_makes_unknown_option():
    prompt = flexmock()
    flexmock(module).should_receive('make_size_path_prompt').with_args(0, '❓ baz.txt').and_return(
        prompt
    )
    flexmock(module.borgmatic.actions.browse.sizes).should_receive('format_size').with_args(
        0
    ).and_return('0 B')
    flexmock(module.textual.widgets.option_list).should_receive('Option').replace_with(flexmock)

    option = module.make_directory_list_option(
        flexmock(path_type='wtf', file_path='foo/bar/baz.txt', link_target=''), ('baz.txt',), 0
    )

    assert option.prompt == prompt
    assert option.prompt_text == '❓ baz.txt (0 B)'
    assert option.path_type == 'wtf'
    assert option.id == 'baz.txt'
