import borgmatic.actions.browse.app
import borgmatic.actions.browse.panels


async def test_browse_app_with_multiple_configs_uses_configuration_files_list():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )

    async with app.run_test() as pilot:
        header = app.query_one(selector='Header')
        header.name == 'borgmatic browse'

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 1
        assert isinstance(
            carousel.panels[0], borgmatic.actions.browse.panels.Configuration_files_list
        )
        assert carousel.panels[0].configs == app.configs

        app.query_one(selector='Logs')
        app.query_one(selector='Footer')


async def test_browse_app_with_one_config_uses_repositories_list():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
        }
    )

    async with app.run_test() as pilot:
        header = app.query_one(selector='Header')
        header.name == 'borgmatic browse'

        carousel = app.query_one(selector='Carousel')
        assert len(carousel.panels) == 1
        assert isinstance(carousel.panels[0], borgmatic.actions.browse.panels.Repositories_list)
        assert carousel.panels[0].config == app.configs['test1.yaml']

        app.query_one(selector='Logs')
        app.query_one(selector='Footer')


async def test_browse_app_key_toggles_logs_panel():
    app = borgmatic.actions.browse.app.Browse_app(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
        }
    )

    async with app.run_test() as pilot:
        logs_panel = app.query_one('#logs')

        await pilot.press('v')
        await pilot.pause()
        assert logs_panel.styles.display == 'block'
