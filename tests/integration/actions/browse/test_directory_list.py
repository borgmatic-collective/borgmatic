from borgmatic.actions.browse import directory_list as module

from flexmock import flexmock
import textual.widgets
import textual.widgets.option_list


def test_add_archive_paths_with_only_duplicate_paths_bails():
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.add_option(textual.widgets.option_list.Option('foo', id='foo'))
    directory_list.add_option(textual.widgets.option_list.Option('bar', id='bar'))
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(directory_list).should_receive('set_options').never()

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(
            flexmock(path_type='-', file_path='etc/foo/one.txt', link_target=''),
            flexmock(path_type='-', file_path='etc/foo/two.txt', link_target=''),
        ),
    )


def test_add_archive_paths_adds_ands_sorts_and_filters_and_deduplicates():
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.add_option(textual.widgets.option_list.Option('📄 foo', id='foo'))
    directory_list.add_option(textual.widgets.option_list.Option('📄 bar', id='bar'))
    directory_list.highlighted = 1
    directory_list.highlighted_option_changed = True
    config = {'repositories': [{'path': 'test.borg'}]}

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(
            flexmock(path_type='d', file_path='etc/quux', link_target=''),
            flexmock(path_type='-', file_path='etc/foo', link_target=''),
            flexmock(path_type='-', file_path='etc/baz', link_target=''),
            flexmock(path_type='d', file_path='root/nope', link_target=''),
            flexmock(path_type='d', file_path='etc/other', link_target=''),
        ),
    )

    assert len(directory_list.options) == 5
    assert directory_list.options[0].prompt == '📁 other'
    assert directory_list.options[0].id == 'other'
    assert directory_list.options[1].prompt == '📁 quux'
    assert directory_list.options[1].id == 'quux'
    assert directory_list.options[2].prompt == '📄 bar'
    assert directory_list.options[2].id == 'bar'
    assert directory_list.options[3].prompt == '📄 baz'
    assert directory_list.options[3].id == 'baz'
    assert directory_list.options[4].prompt == '📄 foo'
    assert directory_list.options[4].id == 'foo'
    assert directory_list.highlighted == 2


def test_add_archive_paths_highlights_first_option_if_highlight_has_not_changed():
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.add_option(textual.widgets.option_list.Option('📄 foo', id='foo'))
    directory_list.add_option(textual.widgets.option_list.Option('📄 bar', id='bar'))
    directory_list.highlighted = None
    directory_list.highlighted_option_changed = False
    config = {'repositories': [{'path': 'test.borg'}]}

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(flexmock(path_type='-', file_path='etc/baz', link_target=''),),
    )

    assert len(directory_list.options) == 3
    assert directory_list.options[0].prompt == '📄 bar'
    assert directory_list.options[0].id == 'bar'
    assert directory_list.options[1].prompt == '📄 baz'
    assert directory_list.options[1].id == 'baz'
    assert directory_list.options[2].prompt == '📄 foo'
    assert directory_list.options[2].id == 'foo'
    assert directory_list.highlighted == 0


def test_add_archive_paths_retains_loading_indicator_at_bottom():
    directory_list = textual.widgets.OptionList()
    directory_list.path_components = ('etc',)
    directory_list.add_option(textual.widgets.option_list.Option('📄 foo', id='foo'))
    directory_list.add_option(textual.widgets.option_list.Option('📄 bar', id='bar'))
    directory_list.add_option(
        textual.widgets.option_list.Option('loading!!!', id='loading-indicator')
    )
    directory_list.highlighted = 0
    directory_list.highlighted_option_changed = True
    config = {'repositories': [{'path': 'test.borg'}]}

    module.add_archive_paths(
        directory_list=directory_list,
        config=config,
        repository=config['repositories'][0],
        archive_name='archive',
        archive_paths=(flexmock(path_type='-', file_path='etc/baz', link_target=''),),
    )

    assert len(directory_list.options) == 4
    assert directory_list.options[0].prompt == '📄 bar'
    assert directory_list.options[0].id == 'bar'
    assert directory_list.options[1].prompt == '📄 baz'
    assert directory_list.options[1].id == 'baz'
    assert directory_list.options[2].prompt == '📄 foo'
    assert directory_list.options[2].id == 'foo'
    assert directory_list.options[3].prompt == 'loading!!!'
    assert directory_list.options[3].id == 'loading-indicator'
    assert directory_list.highlighted == 2


def test_directory_list_with_root_directory_starts_loading_archive_paths():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.workers).should_receive('load_archive_paths').once()
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())

    directory_list = module.Directory_list(
        config=flexmock(), repository=flexmock(), archive_name='archive'
    )
    assert directory_list.border_title == '📁 archive'
    assert len(directory_list.options) == 0
    assert not directory_list.path_loaded.complete


def test_directory_list_with_non_root_directory_relies_on_existing_path_loading_worker():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.workers).should_receive('load_archive_paths').never()
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())

    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=False),
        path_components=('etc',),
    )
    assert directory_list.border_title == '📁 etc'
    assert len(directory_list.options) == 1
    assert directory_list.options[0].prompt == '📁 ..'
    assert directory_list.options[0].id == '..'


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
        path_loaded=flexmock(complete=True),
        path_components=('etc',),
    )
    assert directory_list.border_title == '📁 etc'
    assert len(directory_list.options) == 1
    assert directory_list.options[0].prompt == '📁 ..'
    assert directory_list.options[0].id == '..'


def test_directory_list_on_mount_with_root_directory_skips_adding_archives_paths():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.workers).should_receive('load_archive_paths')
    flexmock(module.borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
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
    flexmock(module).should_receive('add_archive_paths').once()
    directory_list = module.Directory_list(
        config=flexmock(),
        repository=flexmock(),
        archive_name='archive',
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': {}}),
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
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': {}}),
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
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': {}}),
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
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': {}}),
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
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': {}}),
        path_components=('etc',),
    )
    directory_list.add_option(textual.widgets.option_list.Option('zero', id='zero'))
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
        path_loaded=flexmock(complete=False, path_hierarchy={'etc': {}}),
        path_components=('etc',),
    )
    directory_list.add_option(textual.widgets.option_list.Option('zero', id='zero'))
    directory_list.add_option(textual.widgets.option_list.Option('one', id='one'))
    directory_list.highlighted = 1

    directory_list.on_option_list_option_highlighted(event=flexmock())

    assert directory_list.highlighted_option_changed is True
