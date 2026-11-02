from flexmock import flexmock

from borgmatic.actions.browse import archives_list as module


def test_make_archives_list_option_returns_option_with_prompt_text():
    option = flexmock(prompt_text=None)
    flexmock(module.textual.widgets.option_list).should_receive('Option').with_args(
        'archive', id='b33f'
    ).and_return(option)
    archive = {'archive': 'archive', 'id': 'b33f'}

    assert module.make_archives_list_option(archive) == option
    assert option.prompt_text == 'archive'


def test_make_archives_list_option_with_latest_returns_option_with_latest_in_prompt():
    option = flexmock(prompt_text=None)
    flexmock(module.textual.widgets.option_list).should_receive('Option').with_args(
        'archive [dim](latest)[/dim]', id='b33f'
    ).and_return(option)
    archive = {'archive': 'archive', 'id': 'b33f'}

    assert module.make_archives_list_option(archive, latest=True) == option
    assert option.prompt_text == 'archive'
