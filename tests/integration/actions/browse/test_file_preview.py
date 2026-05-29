from borgmatic.actions.browse import file_preview as module

from flexmock import flexmock
import textual.widgets.option_list


def test_file_preview_does_not_raise():
    flexmock(module.borgmatic.actions.browse.loading).should_receive('add_inline_loading_indicator')
    flexmock(module.borgmatic.actions.browse.workers).should_receive('load_file_preview')
    flexmock(module.borgmatic.actions.browse.repositories_list.Repositories_list).should_receive(
        'app'
    ).and_return(flexmock())

    module.Repositories_list(config=flexmock())
