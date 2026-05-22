import asyncio

import borgmatic.actions.browse.app
import borgmatic.actions.browse.carousel
import borgmatic.actions.browse.logs
import borgmatic.actions.browse.panels
import borgmatic.actions.browse.workers

import pytest
from flexmock import flexmock

import textual.widgets.option_list


pytestmark = pytest.mark.asyncio(loop_scope='module')
loop: asyncio.AbstractEventLoop


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


async def test_carousel_next_action_with_multiple_configs_advances_panels():
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
            carousel.panels[0], borgmatic.actions.browse.panels.Configuration_files_list
        )
        assert carousel.panels[0].styles.display == 'none'

        assert isinstance(carousel.panels[1], borgmatic.actions.browse.panels.Repositories_list)
        assert carousel.panels[1].styles.display == 'block'
        assert carousel.panels[1].highlighted == 0
        assert app.focused == carousel.panels[1]


async def test_carousel_next_action_with_one_config_advances_to_next_panel():
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

        assert isinstance(carousel.panels[0], borgmatic.actions.browse.panels.Repositories_list)
        assert carousel.panels[0].styles.display == 'none'

        assert isinstance(carousel.panels[1], borgmatic.actions.browse.panels.Archives_list)
        assert carousel.panels[1].styles.display == 'block'
        assert carousel.panels[1].highlighted == 0
        assert app.focused == carousel.panels[1]


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
            carousel.panels[0], borgmatic.actions.browse.panels.Configuration_files_list
        )
        assert carousel.panels[0].styles.display == 'block'
        assert carousel.panels[0].highlighted == 0

        assert isinstance(carousel.panels[1], borgmatic.actions.browse.panels.Repositories_list)
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
            carousel.panels[0], borgmatic.actions.browse.panels.Configuration_files_list
        )
        assert carousel.panels[0].styles.display == 'none'

        assert isinstance(carousel.panels[1], borgmatic.actions.browse.panels.Repositories_list)
        assert carousel.panels[1].styles.display == 'block'
        assert carousel.panels[1].highlighted == 0
        assert app.focused == carousel.panels[1]


async def test_carousel_next_action_with_no_next_panel_does_not_advance():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )
    flexmock(borgmatic.actions.browse.logs).should_receive('log_to_widget')
    flexmock(borgmatic.actions.browse.carousel).should_receive('make_next_panel').and_return(None)

    async with app.run_test() as pilot:
        await pilot.press('enter')

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 1

        assert isinstance(
            carousel.panels[0], borgmatic.actions.browse.panels.Configuration_files_list
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
            carousel.panels[0], borgmatic.actions.browse.panels.Configuration_files_list
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
            carousel.panels[0], borgmatic.actions.browse.panels.Configuration_files_list
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
            carousel.panels[0], borgmatic.actions.browse.panels.Configuration_files_list
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
            carousel.panels[0], borgmatic.actions.browse.panels.Configuration_files_list
        )
        assert carousel.panels[0].styles.display == 'block'
        assert carousel.panels[0].highlighted == 0

        assert isinstance(carousel.panels[1], borgmatic.actions.browse.panels.Repositories_list)
        assert carousel.panels[1].styles.display == 'none'
        assert app.focused == carousel.panels[0]
