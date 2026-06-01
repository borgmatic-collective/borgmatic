from borgmatic.actions.browse import repositories_list as module


def test_repositories_list_populates_options():
    config = {'repositories': [{'path': 'test1.borg'}, {'path': 'test2.borg', 'label': 'two'}]}

    repositories_list = module.Repositories_list(config=config)
    assert len(repositories_list.options) == 2
    assert repositories_list.options[0].prompt == 'test1.borg'
    assert repositories_list.options[0].id == 0
    assert repositories_list.options[1].prompt == 'two'
    assert repositories_list.options[1].id == 1
