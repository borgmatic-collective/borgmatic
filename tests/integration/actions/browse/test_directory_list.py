import rich.console
import rich.text
import textual.widgets
import textual.widgets.option_list
from flexmock import flexmock

from borgmatic.actions.browse import directory_list as module
from borgmatic.actions.browse.workers import Directory


def rendered_text(renderable):
    '''
    Given a Rich renderable, return its rendered plain text.
    '''
    console = rich.console.Console(width=60, color_system=None)

    with console.capture() as capture:
        console.print(renderable, end='')

    return capture.get()


def make_option(prompt, option_id):
    '''
    Make a textual.widgets.option_list.Option with the given prompt and ID, stashing the prompt as
    prompt_text the way that real directory list and loading indicator options do.
    '''
    option = textual.widgets.option_list.Option(prompt, id=option_id)
    option.prompt_text = prompt

    return option


def test_make_size_path_prompt_aligns_paths_regardless_of_size_length():
    bytes_prompt = module.make_size_path_prompt(0, 'path')
    kilobytes_prompt = module.make_size_path_prompt(1024, 'path')

    assert isinstance(bytes_prompt, rich.text.Text)
    assert rendered_text(bytes_prompt).index('path') == rendered_text(kilobytes_prompt).index(
        'path'
    )


def test_make_size_path_prompt_aligns_bytes_number_with_larger_size_numbers():
    bytes_text = rendered_text(module.make_size_path_prompt(358, 'path'))
    kilobytes_text = rendered_text(module.make_size_path_prompt(1024, 'path'))

    assert bytes_text.index('358') + len('358') == kilobytes_text.index('1.02') + len('1.02')


def test_add_archive_paths_with_only_duplicate_paths_bails():
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.path_loaded = flexmock(path_hierarchy={})
    directory_list.add_option(make_option('foo', option_id='foo'))
    directory_list.add_option(make_option('bar', option_id='bar'))
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(directory_list).should_receive('clear_options').never()
    flexmock(directory_list).should_receive('add_options').never()

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(
            flexmock(path_type='-', file_path='etc/foo/one.txt', link_target='', size=1),
            flexmock(path_type='-', file_path='etc/foo/two.txt', link_target='', size=1),
        ),
    )


def test_add_archive_paths_adds_ands_sorts_and_filters_and_deduplicates():
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.path_loaded = flexmock(path_hierarchy={})
    directory_list.add_option(make_option('📄 foo', option_id='foo'))
    directory_list.add_option(make_option('📄 bar', option_id='bar'))
    directory_list.highlighted = 1
    directory_list.highlighted_option_changed = True
    config = {'repositories': [{'path': 'test.borg'}]}

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(
            flexmock(path_type='d', file_path='etc/quux', link_target='', size=0),
            flexmock(path_type='-', file_path='etc/foo', link_target='', size=0),
            flexmock(path_type='-', file_path='etc/baz', link_target='', size=0),
            flexmock(path_type='d', file_path='root/nope', link_target='', size=0),
            flexmock(path_type='d', file_path='etc/other', link_target='', size=0),
        ),
    )

    assert len(directory_list.options) == 5
    assert directory_list.options[0].prompt_text == '📁 other (0 B)'
    assert directory_list.options[0].id == 'other'
    assert directory_list.options[1].prompt_text == '📁 quux (0 B)'
    assert directory_list.options[1].id == 'quux'
    assert directory_list.options[2].prompt_text == '📄 bar'
    assert directory_list.options[2].id == 'bar'
    assert directory_list.options[3].prompt_text == '📄 baz (0 B)'
    assert directory_list.options[3].id == 'baz'
    assert directory_list.options[4].prompt_text == '📄 foo (0 B)'
    assert directory_list.options[4].id == 'foo'
    assert directory_list.highlighted == 2


def test_add_archive_paths_updates_existing_option_size():
    hierarchy = {}

    for file_name in ('bar.txt', 'baz.txt'):
        module.borgmatic.actions.browse.workers.record_path(
            archive_path=module.borgmatic.actions.browse.archive.Archive_path(
                '-', f'etc/foo/{file_name}', '', 1024
            ),
            hierarchy=hierarchy,
            path_components=('etc', 'foo', file_name),
        )

    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.path_loaded = flexmock(path_hierarchy=hierarchy)
    # The option's size as of before baz.txt loaded.
    directory_list.add_option(make_option('📁 foo (1.02 kB)', option_id='foo'))
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(directory_list).should_call('replace_option_prompt').with_args('foo', object).once()
    flexmock(directory_list).should_receive('clear_options').never()
    flexmock(directory_list).should_receive('add_options').never()

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(
            flexmock(path_type='-', file_path='etc/foo/baz.txt', link_target='', size=1024),
        ),
    )

    assert directory_list.options[0].prompt_text == '📁 foo (2.05 kB)'


def test_add_archive_paths_does_not_repaint_unchanged_size():
    hierarchy = {}
    module.borgmatic.actions.browse.workers.record_path(
        archive_path=module.borgmatic.actions.browse.archive.Archive_path(
            '-', 'etc/foo/bar.txt', '', 2048
        ),
        hierarchy=hierarchy,
        path_components=('etc', 'foo', 'bar.txt'),
    )
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.path_loaded = flexmock(path_hierarchy=hierarchy)
    directory_list.add_option(make_option('📁 foo (2.05 kB)', option_id='foo'))
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(directory_list).should_receive('replace_option_prompt').never()
    flexmock(directory_list).should_receive('clear_options').never()
    flexmock(directory_list).should_receive('add_options').never()

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(
            flexmock(path_type='-', file_path='etc/foo/bar.txt', link_target='', size=2048),
        ),
    )


def test_add_archive_paths_ignores_link_target_for_directory_row():
    hierarchy = {}
    module.borgmatic.actions.browse.workers.record_path(
        archive_path=module.borgmatic.actions.browse.archive.Archive_path(
            'l', 'etc/foo/link', '/home/foo/.git', 0
        ),
        hierarchy=hierarchy,
        path_components=('etc', 'foo', 'link'),
    )
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.path_loaded = flexmock(path_hierarchy=hierarchy)
    directory_list.add_option(make_option('📁 foo (0 B)', option_id='foo'))
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(directory_list).should_receive('replace_option_prompt').never()
    flexmock(directory_list).should_receive('clear_options').never()
    flexmock(directory_list).should_receive('add_options').never()

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(
            flexmock(path_type='l', file_path='etc/foo/link', link_target='/home/foo/.git', size=0),
        ),
    )


def test_add_archive_paths_computes_one_size_update_per_directory_for_a_batch():
    archive_paths = tuple(
        module.borgmatic.actions.browse.archive.Archive_path('-', f'etc/foo/{name}', '', 100)
        for name in ('one', 'two', 'three')
    )
    hierarchy = {}
    for archive_path in archive_paths:
        module.borgmatic.actions.browse.workers.record_path(
            archive_path, hierarchy, ('etc', 'foo', archive_path.file_path.rsplit('/', 1)[1])
        )
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.path_loaded = flexmock(path_hierarchy=hierarchy)
    directory_list.add_option(make_option('📁 foo (100 B)', option_id='foo'))
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(directory_list).should_receive('replace_option_prompt').once()
    flexmock(directory_list).should_receive('clear_options').never()
    flexmock(directory_list).should_receive('add_options').never()

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=archive_paths,
    )

    assert directory_list.get_option('foo').prompt_text == '📁 foo (300 B)'


def test_add_archive_paths_highlights_first_option_if_highlight_has_not_changed():
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.path_loaded = flexmock(path_hierarchy={})
    directory_list.add_option(make_option('📄 foo', option_id='foo'))
    directory_list.add_option(make_option('📄 bar', option_id='bar'))
    directory_list.highlighted = None
    directory_list.highlighted_option_changed = False
    config = {'repositories': [{'path': 'test.borg'}]}

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(flexmock(path_type='-', file_path='etc/baz', link_target='', size=0),),
    )

    assert len(directory_list.options) == 3
    assert directory_list.options[0].prompt_text == '📄 bar'
    assert directory_list.options[0].id == 'bar'
    assert directory_list.options[1].prompt_text == '📄 baz (0 B)'
    assert directory_list.options[1].id == 'baz'
    assert directory_list.options[2].prompt_text == '📄 foo'
    assert directory_list.options[2].id == 'foo'
    assert directory_list.highlighted == 0


def test_add_archive_paths_retains_loading_indicator_at_bottom():
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.path_loaded = flexmock(path_hierarchy={})
    directory_list.add_option(make_option('📄 foo', option_id='foo'))
    directory_list.add_option(make_option('📄 bar', option_id='bar'))
    directory_list.add_option(make_option('loading!!!', option_id='loading-indicator'))
    directory_list.highlighted = 0
    directory_list.highlighted_option_changed = True
    config = {'repositories': [{'path': 'test.borg'}]}

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(flexmock(path_type='-', file_path='etc/baz', link_target='', size=0),),
    )

    assert len(directory_list.options) == 4
    assert directory_list.options[0].prompt_text == '📄 bar'
    assert directory_list.options[0].id == 'bar'
    assert directory_list.options[1].prompt_text == '📄 baz (0 B)'
    assert directory_list.options[1].id == 'baz'
    assert directory_list.options[2].prompt_text == '📄 foo'
    assert directory_list.options[2].id == 'foo'
    assert directory_list.options[3].prompt_text == 'loading!!!'
    assert directory_list.options[3].id == 'loading-indicator'
    assert directory_list.highlighted == 2


def test_directory_list_with_root_directory_adds_loading_indicator():
    flexmock(module.borgmatic.actions.browse.loading).should_receive(
        'add_inline_loading_indicator'
    ).once()

    directory_list = module.Directory_list(
        config=flexmock(), repository=flexmock(), archive_name='archive'
    )
    assert directory_list.border_title == '📁 archive (0 B)'
    assert len(directory_list.options) == 0
    assert not directory_list.path_loaded.complete


def test_directory_list_with_already_complete_loading_skips_loading_indicator():
    flexmock(module.borgmatic.actions.browse.loading).should_receive(
        'add_inline_loading_indicator'
    ).never()
    flexmock(module.borgmatic.actions.browse.workers).should_receive('load_archive_paths').never()
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())

    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=True, path_hierarchy={}),
        path_components=('etc',),
    )
    assert directory_list.border_title == '📁 etc (0 B)'
    assert len(directory_list.options) == 1
    assert directory_list.options[0].prompt_text == '📁 ..'
    assert directory_list.options[0].id == '..'


def test_directory_list_on_mount_with_root_directory_loads_archive_paths():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    flexmock(module.borgmatic.actions.browse.workers).should_receive('load_archive_paths').once()
    flexmock(module).should_receive('add_archive_paths').never()
    directory_list = module.Directory_list(
        config=flexmock(), repository=flexmock(), archive_name='archive'
    )
    flexmock(directory_list.path_loaded).should_receive('subscribe')

    directory_list.on_mount()


def test_directory_list_on_mount_with_non_root_directory_adds_archive_paths():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    flexmock(module.borgmatic.actions.browse.workers).should_receive('load_archive_paths').never()
    flexmock(module).should_receive('add_archive_paths').once()
    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': Directory()}),
        path_components=('etc',),
    )
    flexmock(directory_list.path_loaded).should_receive('subscribe')

    directory_list.on_mount()


def test_on_archive_path_loaded_with_loading_done_signal_removes_loading_indicator():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    flexmock(module).should_receive('add_archive_paths').never()
    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': Directory()}),
        path_components=('etc',),
    )
    directory_list.timer = flexmock(stop=lambda: None)
    flexmock(directory_list).should_receive('remove_option').once()

    directory_list.on_archive_path_loaded(data=module.borgmatic.actions.browse.workers.LOADING_DONE)


def test_on_archive_path_loaded_with_path_loaded_signal_adds_archive_path():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    flexmock(module).should_receive('add_archive_paths').once()
    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': Directory()}),
        path_components=('etc',),
    )
    flexmock(directory_list).should_receive('remove_option').never()

    directory_list.on_archive_path_loaded(data=flexmock())


def test_directory_list_on_option_list_option_highlighted_with_highlighted_none_marks_it_unchanged():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': Directory()}),
        path_components=('etc',),
    )
    directory_list.highlighted = None

    directory_list.on_option_list_option_highlighted(event=flexmock())

    assert directory_list.highlighted_option_changed is False


def test_directory_list_on_option_list_option_highlighted_with_highlighted_zero_marks_it_unchanged():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': Directory()}),
        path_components=('etc',),
    )
    directory_list.add_option(make_option('zero', option_id='zero'))
    directory_list.highlighted = 0

    directory_list.on_option_list_option_highlighted(event=flexmock())

    assert directory_list.highlighted_option_changed is False


def test_directory_list_on_option_list_option_highlighted_with_highlighted_non_zero_marks_it_changed():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': Directory()}),
        path_components=('etc',),
    )
    directory_list.add_option(make_option('zero', option_id='zero'))
    directory_list.add_option(make_option('one', option_id='one'))
    directory_list.highlighted = 1

    directory_list.on_option_list_option_highlighted(event=flexmock())

    assert directory_list.highlighted_option_changed is True


def test_directory_list_update_border_title_reflects_newly_loaded_directory_size():
    hierarchy = {'etc': Directory()}
    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=True, path_hierarchy=hierarchy),
        path_components=('etc',),
    )
    assert directory_list.border_title == '📁 etc (0 B)'

    module.borgmatic.actions.browse.workers.record_path(
        archive_path=module.borgmatic.actions.browse.archive.Archive_path(
            '-', 'etc/bar.txt', '', 1024
        ),
        hierarchy=hierarchy,
        path_components=('etc', 'bar.txt'),
    )

    directory_list.update_border_title()

    assert directory_list.border_title == '📁 etc (1.02 kB)'


def test_directory_list_update_border_title_reflects_newly_loaded_archive_size():
    hierarchy = {'etc': Directory()}
    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=True, path_hierarchy=hierarchy),
    )
    assert directory_list.border_title == '📁 archive (0 B)'

    for file_path in ('etc/bar.txt', 'foo.txt'):
        module.borgmatic.actions.browse.workers.record_path(
            archive_path=module.borgmatic.actions.browse.archive.Archive_path(
                '-', file_path, '', 512
            ),
            hierarchy=hierarchy,
            path_components=tuple(file_path.split('/')),
        )

    directory_list.update_border_title()

    assert directory_list.border_title == '📁 archive (1.02 kB)'
