from flexmock import flexmock

from borgmatic.borg import environment as module


def test_make_environment_with_passcommand_should_call_it_and_set_passphrase_file_descriptor_in_environment():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return('passphrase')
    flexmock(module.os).should_receive('pipe').and_return((3, 4))
    flexmock(module.os).should_receive('write')
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    environment = module.make_environment({'encryption_passcommand': 'command'})

    assert not environment.get('BORG_PASSCOMMAND')
    assert environment.get('BORG_PASSPHRASE_FD') == '3'


def test_make_environment_with_passphrase_should_set_environment():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    flexmock(module.os.environ).should_receive('get').and_return(None)
    environment = module.make_environment({'encryption_passphrase': 'pass'})

    assert environment.get('BORG_PASSPHRASE') == 'pass'


def test_make_environment_with_ssh_command_should_set_environment():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    flexmock(module.os.environ).should_receive('get').and_return(None)
    environment = module.make_environment({'ssh_command': 'ssh -C'})

    assert environment.get('BORG_RSH') == 'ssh -C'


def test_make_environment_without_configuration_sets_certain_environment_variables():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    flexmock(module.os.environ).should_receive('get').and_return(None)
    environment = module.make_environment({})

    # Default environment variables.
    assert environment == {
        'BORG_EXIT_CODES': 'modern',
        'BORG_RELOCATED_REPO_ACCESS_IS_OK': 'no',
        'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK': 'no',
    }


def test_make_environment_without_configuration_does_not_set_certain_environment_variables_if_already_set():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    flexmock(module.os.environ).should_receive('get').with_args(
        'BORG_RELOCATED_REPO_ACCESS_IS_OK'
    ).and_return('yup')
    flexmock(module.os.environ).should_receive('get').with_args(
        'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK'
    ).and_return('nah')
    environment = module.make_environment({})

    assert environment == {'BORG_EXIT_CODES': 'modern'}


def test_make_environment_with_relocated_repo_access_true_should_set_environment_yes():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    flexmock(module.os.environ).should_receive('get').and_return(None)
    environment = module.make_environment({'relocated_repo_access_is_ok': True})

    assert environment.get('BORG_RELOCATED_REPO_ACCESS_IS_OK') == 'yes'


def test_make_environment_with_relocated_repo_access_false_should_set_environment_no():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    flexmock(module.os.environ).should_receive('get').and_return(None)
    environment = module.make_environment({'relocated_repo_access_is_ok': False})

    assert environment.get('BORG_RELOCATED_REPO_ACCESS_IS_OK') == 'no'


def test_make_environment_check_i_know_what_i_am_doing_true_should_set_environment_YES():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    flexmock(module.os.environ).should_receive('get').and_return(None)
    environment = module.make_environment({'check_i_know_what_i_am_doing': True})

    assert environment.get('BORG_CHECK_I_KNOW_WHAT_I_AM_DOING') == 'YES'


def test_make_environment_check_i_know_what_i_am_doing_false_should_set_environment_NO():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    flexmock(module.os.environ).should_receive('get').and_return(None)
    environment = module.make_environment({'check_i_know_what_i_am_doing': False})

    assert environment.get('BORG_CHECK_I_KNOW_WHAT_I_AM_DOING') == 'NO'


def test_make_environment_with_integer_variable_value():
    flexmock(module.borgmatic.hooks.dispatch).should_receive('call_hook').and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    flexmock(module.os.environ).should_receive('get').and_return(None)
    environment = module.make_environment({'borg_files_cache_ttl': 40})
    assert environment.get('BORG_FILES_CACHE_TTL') == '40'
