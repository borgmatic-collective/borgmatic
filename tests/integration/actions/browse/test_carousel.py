import pytest
import textual.widgets.option_list
from flexmock import flexmock

import borgmatic.actions.browse.app
import borgmatic.actions.browse.archive
import borgmatic.actions.browse.carousel
import borgmatic.actions.browse.loading
import borgmatic.actions.browse.logs
import borgmatic.actions.browse.workers
from borgmatic.actions.browse import carousel as module


def test_make_next_panel_with_configuration_files_list_returns_repositories_list():
    configs = {'test.yaml': {'repositories': [{'path': 'test.borg'}]}}

    repositories_list = module.make_next_panel(
        focused_panel=borgmatic.actions.browse.configuration_files_list.Configuration_files_list(
            configs
        ),
        option_id='test.yaml',
    )

    assert isinstance(
        repositories_list, borgmatic.actions.browse.repositories_list.Repositories_list
    )
    assert repositories_list.config == configs['test.yaml']


def test_make_next_panel_with_repositories_list_returns_archives_list():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(borgmatic.actions.browse.workers).should_receive('add_repository_archives')
    flexmock(borgmatic.actions.browse.archives_list.Archives_list).should_receive('app').and_return(
        flexmock()
    )

    archives_list = module.make_next_panel(
        focused_panel=borgmatic.actions.browse.repositories_list.Repositories_list(config),
        option_id=0,
    )

    assert isinstance(archives_list, borgmatic.actions.browse.archives_list.Archives_list)
    assert archives_list.config == config
    assert archives_list.repository == config['repositories'][0]


def test_make_next_panel_with_archives_list_returns_directory_list():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(borgmatic.actions.browse.workers).should_receive('add_repository_archives')
    flexmock(borgmatic.actions.browse.workers).should_receive('load_archive_paths')
    flexmock(borgmatic.actions.browse.archives_list.Archives_list).should_receive('app').and_return(
        flexmock()
    )
    flexmock(borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())

    directory_list = module.make_next_panel(
        focused_panel=borgmatic.actions.browse.archives_list.Archives_list(
            config, config['repositories'][0]
        ),
        option_id='archive',
    )

    assert isinstance(directory_list, borgmatic.actions.browse.directory_list.Directory_list)
    assert directory_list.config == config
    assert directory_list.repository == config['repositories'][0]


def test_make_next_panel_with_root_directory_list_and_selected_directory_option_returns_new_directory_list():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(borgmatic.actions.browse.workers).should_receive('load_archive_paths')
    flexmock(borgmatic.actions.browse.workers).should_receive('Archive_path_loaded').replace_with(
        flexmock(
            path_hierarchy={
                'etc': {},
            },
            complete=False,
        ),
    )
    flexmock(borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    focused_panel = borgmatic.actions.browse.directory_list.Directory_list(
        config, config['repositories'][0], 'archive'
    )
    flexmock(focused_panel).should_receive('get_option').and_return(flexmock(prompt='📁 etc'))

    directory_list = module.make_next_panel(focused_panel=focused_panel, option_id='etc')

    assert isinstance(directory_list, borgmatic.actions.browse.directory_list.Directory_list)
    assert directory_list.config == config
    assert directory_list.repository == config['repositories'][0]
    assert directory_list.archive_name == 'archive'
    assert directory_list.path_components == ('etc',)


def test_make_next_panel_with_non_root_directory_list_and_selected_directory_option_returns_new_directory_list():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(borgmatic.actions.browse.workers).should_receive('load_archive_paths')
    flexmock(borgmatic.actions.browse.workers).should_receive('Archive_path_loaded').replace_with(
        flexmock(
            path_hierarchy={
                'etc': {
                    'borgmatic': {},
                },
            },
            complete=False,
        ),
    )
    flexmock(borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    focused_panel = borgmatic.actions.browse.directory_list.Directory_list(
        config,
        config['repositories'][0],
        'archive',
        path_components=('etc',),
    )
    flexmock(focused_panel).should_receive('get_option').and_return(flexmock(prompt='📁 borgmatic'))

    directory_list = module.make_next_panel(focused_panel=focused_panel, option_id='borgmatic')

    assert isinstance(directory_list, borgmatic.actions.browse.directory_list.Directory_list)
    assert directory_list.config == config
    assert directory_list.repository == config['repositories'][0]
    assert directory_list.archive_name == 'archive'
    assert directory_list.path_components == ('etc', 'borgmatic')


def test_make_next_panel_with_root_directory_list_and_selected_file_option_returns_new_file_preview():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(borgmatic.actions.browse.workers).should_receive('load_archive_paths')
    flexmock(borgmatic.actions.browse.workers).should_receive('load_file_preview')
    flexmock(borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    flexmock(borgmatic.actions.browse.file_preview.File_preview).should_receive('app').and_return(
        flexmock()
    )
    focused_panel = borgmatic.actions.browse.directory_list.Directory_list(
        config, config['repositories'][0], 'archive'
    )
    flexmock(focused_panel).should_receive('get_option').and_return(
        flexmock(prompt='📄 config.yaml')
    )

    directory_list = module.make_next_panel(focused_panel=focused_panel, option_id='config.yaml')

    assert isinstance(directory_list, borgmatic.actions.browse.file_preview.File_preview)
    assert directory_list.config == config
    assert directory_list.repository == config['repositories'][0]
    assert directory_list.archive_name == 'archive'
    assert directory_list.file_path == 'config.yaml'


def test_make_next_panel_with_non_root_directory_list_and_selected_file_option_returns_new_file_preview():
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(borgmatic.actions.browse.workers).should_receive('load_archive_paths')
    flexmock(borgmatic.actions.browse.workers).should_receive('load_file_preview')
    flexmock(borgmatic.actions.browse.workers).should_receive('Archive_path_loaded').replace_with(
        flexmock(
            path_hierarchy={
                'etc': {
                    'borgmatic': {
                        'config.yaml': borgmatic.actions.browse.archive.Archive_path(
                            '-', 'config.yaml', ''
                        ),
                    },
                },
            },
            complete=False,
        ),
    )
    flexmock(borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    flexmock(borgmatic.actions.browse.file_preview.File_preview).should_receive('app').and_return(
        flexmock()
    )
    focused_panel = borgmatic.actions.browse.directory_list.Directory_list(
        config,
        config['repositories'][0],
        'archive',
        path_components=('etc', 'borgmatic'),
    )
    flexmock(focused_panel).should_receive('get_option').and_return(
        flexmock(prompt='📄 config.yaml')
    )

    directory_list = module.make_next_panel(focused_panel=focused_panel, option_id='config.yaml')

    assert isinstance(directory_list, borgmatic.actions.browse.file_preview.File_preview)
    assert directory_list.config == config
    assert directory_list.repository == config['repositories'][0]
    assert directory_list.archive_name == 'archive'
    assert directory_list.file_path == 'etc/borgmatic/config.yaml'


def test_make_next_panel_with_unsupported_focused_panel_returns_none():
    assert module.make_next_panel(focused_panel=flexmock(), option_id='hmmm') is None


@pytest.mark.parametrize('icon', ('🔗', '🚰', '🐙'))
def test_make_next_panel_with_directory_list_and_unsupported_selected_option_returns_none(icon):
    config = {'repositories': [{'path': 'test.borg'}]}
    flexmock(borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(borgmatic.actions.browse.workers).should_receive('load_archive_paths')
    flexmock(borgmatic.actions.browse.directory_list.Directory_list).should_receive(
        'app'
    ).and_return(flexmock())
    focused_panel = borgmatic.actions.browse.directory_list.Directory_list(
        config, config['repositories'][0], 'archive'
    )
    flexmock(focused_panel).should_receive('get_option').and_return(
        flexmock(prompt=f'{icon} config.yaml')
    )

    assert module.make_next_panel(focused_panel=focused_panel, option_id='config.yaml') is None


async def test_carousel_previous_action_with_multiple_configs_does_not_raise():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')

    async with app.run_test() as pilot:
        await pilot.press('left')


async def test_carousel_previous_action_with_one_config_does_not_raise():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')

    async with app.run_test() as pilot:
        await pilot.press('left')


async def test_carousel_next_action_with_multiple_configs_advances_panel():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')

    async with app.run_test() as pilot:
        await pilot.press('enter')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 2

        assert isinstance(
            carousel.panels[0],
            borgmatic.actions.browse.configuration_files_list.Configuration_files_list,
        )
        assert carousel.panels[0].styles.display == 'none'

        assert isinstance(
            carousel.panels[1], borgmatic.actions.browse.repositories_list.Repositories_list
        )
        assert carousel.panels[1].styles.display == 'block'
        assert carousel.panels[1].highlighted == 0
        assert app.focused == carousel.panels[1]


async def test_carousel_next_action_with_one_config_advances_panel():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')
    flexmock(borgmatic.actions.browse.workers).should_receive('add_repository_archives')

    async with app.run_test() as pilot:
        await pilot.press('enter')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 2

        assert isinstance(
            carousel.panels[0], borgmatic.actions.browse.repositories_list.Repositories_list
        )
        assert carousel.panels[0].styles.display == 'none'

        assert isinstance(carousel.panels[1], borgmatic.actions.browse.archives_list.Archives_list)
        assert carousel.panels[1].styles.display == 'block'
        assert carousel.panels[1].highlighted == 0
        assert app.focused == carousel.panels[1]


async def test_carousel_next_action_with_no_next_panel_does_not_advance():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')
    flexmock(borgmatic.actions.browse.workers).should_receive('add_repository_archives')
    flexmock(module).should_receive('make_next_panel')

    async with app.run_test() as pilot:
        await pilot.press('enter')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 1

        assert isinstance(
            carousel.panels[0], borgmatic.actions.browse.repositories_list.Repositories_list
        )
        assert carousel.panels[0].styles.display == 'block'
        assert app.focused == carousel.panels[0]


async def test_carousel_next_action_and_previous_action_returns_to_original_panel():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')

    async with app.run_test() as pilot:
        await pilot.press('enter')
        await pilot.press('left')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 2

        assert isinstance(
            carousel.panels[0],
            borgmatic.actions.browse.configuration_files_list.Configuration_files_list,
        )
        assert carousel.panels[0].styles.display == 'block'
        assert carousel.panels[0].highlighted == 0

        assert isinstance(
            carousel.panels[1], borgmatic.actions.browse.repositories_list.Repositories_list
        )
        assert carousel.panels[1].styles.display == 'none'
        assert app.focused == carousel.panels[0]


async def test_carousel_next_action_and_previous_action_and_next_action_reuses_next_panel():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')
    flexmock(borgmatic.actions.browse.carousel).should_call('make_next_panel').once()

    async with app.run_test() as pilot:
        await pilot.press('enter')
        await pilot.press('left')
        await pilot.press('enter')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 2

        assert isinstance(
            carousel.panels[0],
            borgmatic.actions.browse.configuration_files_list.Configuration_files_list,
        )
        assert carousel.panels[0].styles.display == 'none'

        assert isinstance(
            carousel.panels[1], borgmatic.actions.browse.repositories_list.Repositories_list
        )
        assert carousel.panels[1].styles.display == 'block'
        assert carousel.panels[1].highlighted == 0
        assert app.focused == carousel.panels[1]


async def test_carousel_next_action_with_multiple_configs_and_no_next_panel_does_not_advance():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')
    flexmock(module).should_receive('make_next_panel').and_return(None)

    async with app.run_test() as pilot:
        await pilot.press('enter')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 1

        assert isinstance(
            carousel.panels[0],
            borgmatic.actions.browse.configuration_files_list.Configuration_files_list,
        )
        assert carousel.panels[0].styles.display == 'block'
        assert carousel.panels[0].highlighted == 0
        assert app.focused == carousel.panels[0]


async def test_carousel_next_action_and_previous_action_and_down_truncates_next_panel():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')

    async with app.run_test() as pilot:
        await pilot.press('enter')
        await pilot.press('left')
        await pilot.press('down')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 1

        assert isinstance(
            carousel.panels[0],
            borgmatic.actions.browse.configuration_files_list.Configuration_files_list,
        )
        assert carousel.panels[0].styles.display == 'block'
        assert carousel.panels[0].highlighted == 1
        assert app.focused == carousel.panels[0]


async def test_carousel_down_does_not_raise():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')

    async with app.run_test() as pilot:
        await pilot.press('down')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 1

        assert isinstance(
            carousel.panels[0],
            borgmatic.actions.browse.configuration_files_list.Configuration_files_list,
        )
        assert carousel.panels[0].styles.display == 'block'
        assert carousel.panels[0].highlighted == 1
        assert app.focused == carousel.panels[0]


async def test_carousel_up_does_not_raise():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')

    async with app.run_test() as pilot:
        await pilot.press('down')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 1

        assert isinstance(
            carousel.panels[0],
            borgmatic.actions.browse.configuration_files_list.Configuration_files_list,
        )
        assert carousel.panels[0].styles.display == 'block'
        assert carousel.panels[0].highlighted == 1
        assert app.focused == carousel.panels[0]


async def test_carousel_next_action_and_select_dot_dot_returns_to_original_panel():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')

    async with app.run_test() as pilot:
        await pilot.press('enter')

        carousel = app.query_one(selector='Carousel')
        carousel.panels[1].options[0] = textual.widgets.option_list.Option('..', id='..')

        await pilot.press('enter')

        assert len(carousel.panels) == 2

        assert isinstance(
            carousel.panels[0],
            borgmatic.actions.browse.configuration_files_list.Configuration_files_list,
        )
        assert carousel.panels[0].styles.display == 'block'
        assert carousel.panels[0].highlighted == 0

        assert isinstance(
            carousel.panels[1], borgmatic.actions.browse.repositories_list.Repositories_list
        )
        assert carousel.panels[1].styles.display == 'none'
        assert app.focused == carousel.panels[0]
