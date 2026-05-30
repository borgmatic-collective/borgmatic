from borgmatic.actions.browse import configuration_files_list as module

from flexmock import flexmock


def test_configuration_files_list_adds_config_paths_as_options():
    flexmock(module.os.path).should_receive('expanduser').and_return('/home/user')

    configuration_files_list = module.Configuration_files_list(
        configs={
            'test1.yaml': {'repositories': [{'path': 'test1.borg'}]},
            'test2.yaml': {'repositories': [{'path': 'test2.borg'}]},
        }
    )

    assert len(configuration_files_list.options) == 2
    assert configuration_files_list.options[0].prompt == 'test1.yaml'
    assert configuration_files_list.options[0].id == 'test1.yaml'
    assert configuration_files_list.options[1].prompt == 'test2.yaml'
    assert configuration_files_list.options[1].id == 'test2.yaml'


def test_configuration_files_list_collapses_home_directory_in_config_path_option():
    flexmock(module.os.path).should_receive('expanduser').and_return('/home/user')

    configuration_files_list = module.Configuration_files_list(
        configs={
            '/home/user/test.yaml': {'repositories': [{'path': '/home/user/test.borg'}]},
        }
    )

    assert len(configuration_files_list.options) == 1
    assert configuration_files_list.options[0].prompt == '~/test.yaml'
    assert configuration_files_list.options[0].id == '/home/user/test.yaml'
