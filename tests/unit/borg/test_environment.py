from flexmock import flexmock

from borgmatic.borg import environment as module


def test_make_environment_with_passcommand_should_call_it_and_set_passphrase_file_descriptor_in_environment():
    flexmock(module.os).should_receive('environ').and_return(
        {'USER': 'root', 'BORG_PASSCOMMAND': 'nope'}
    )
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.borgmatic.borg.passcommand).should_receive(
        'get_passphrase_from_passcommand'
    ).and_return('passphrase')
    flexmock(module.os).should_receive('pipe').and_return((3, 4))
    flexmock(module.os).should_receive('write')
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    environment = module.make_environment({'encryption_passcommand': 'command'})

    assert environment.get('BORG_PASSPHRASE') is None
    assert environment.get('BORG_PASSCOMMAND') is None
    assert environment.get('BORG_PASSPHRASE_FD') == '3'


def test_make_environment_with_passphrase_should_set_passphrase_file_descriptor_in_environment():
    flexmock(module.os).should_receive('environ').and_return(
        {'USER': 'root', 'BORG_PASSPHRASE': 'nope', 'BORG_PASSCOMMAND': 'nope'}
    )
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).replace_with(lambda value, config: value)
    flexmock(module.borgmatic.borg.passcommand).should_receive(
        'get_passphrase_from_passcommand'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').and_return((3, 4))
    flexmock(module.os).should_receive('write')
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    environment = module.make_environment({'encryption_passphrase': 'pass'})

    assert environment.get('BORG_PASSPHRASE') is None
    assert environment.get('BORG_PASSCOMMAND') is None
    assert environment.get('BORG_PASSPHRASE_FD') == '3'


def test_make_environment_with_credential_tag_passphrase_should_load_it_and_set_passphrase_file_descriptor_in_environment():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    config = {'encryption_passphrase': '{credential systemd pass}'}
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential',
    ).with_args('{credential systemd pass}', config).and_return('pass')
    flexmock(module.borgmatic.borg.passcommand).should_receive(
        'get_passphrase_from_passcommand'
    ).never()
    flexmock(module.os).should_receive('pipe').and_return((3, 4))
    flexmock(module.os).should_receive('write')
    flexmock(module.os).should_receive('close')
    flexmock(module.os).should_receive('set_inheritable')

    environment = module.make_environment(config)

    assert environment.get('BORG_PASSPHRASE') is None
    assert environment.get('BORG_PASSPHRASE_FD') == '3'


def test_make_environment_with_ssh_command_should_set_environment():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'ssh_command': 'ssh -C'})

    assert environment.get('BORG_RSH') == 'ssh -C'


def test_make_environment_without_configuration_sets_certain_environment_variables():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({})

    # Default environment variables.
    assert environment == {
        'USER': 'root',
        'BORG_EXIT_CODES': 'modern',
        'BORG_RELOCATED_REPO_ACCESS_IS_OK': 'NO',
        'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK': 'NO',
        'BORG_USE_CHUNKS_ARCHIVE': 'NO',
        'BORG_DEBUG_PASSPHRASE': 'NO',
        'BORG_DISPLAY_PASSPHRASE': 'NO',
    }


def test_make_environment_without_configuration_passes_through_default_environment_variables_untouched():
    flexmock(module.os).should_receive('environ').and_return(
        {
            'USER': 'root',
            'BORG_RELOCATED_REPO_ACCESS_IS_OK': 'yup',
            'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK': 'nah',
            'BORG_USE_CHUNKS_ARCHIVE': 'yup',
            'BORG_DEBUG_PASSPHRASE': 'nah',
            'BORG_DISPLAY_PASSPHRASE': 'yup',
        }
    )
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({})

    assert environment == {
        'USER': 'root',
        'BORG_RELOCATED_REPO_ACCESS_IS_OK': 'yup',
        'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK': 'nah',
        'BORG_USE_CHUNKS_ARCHIVE': 'yup',
        'BORG_DEBUG_PASSPHRASE': 'nah',
        'BORG_DISPLAY_PASSPHRASE': 'yup',
        'BORG_EXIT_CODES': 'modern',
    }


def test_make_environment_with_relocated_repo_access_true_should_set_environment_YES():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'relocated_repo_access_is_ok': True})

    assert environment.get('BORG_RELOCATED_REPO_ACCESS_IS_OK') == 'YES'


def test_make_environment_with_relocated_repo_access_false_should_set_environment_NO():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'relocated_repo_access_is_ok': False})

    assert environment.get('BORG_RELOCATED_REPO_ACCESS_IS_OK') == 'NO'


def test_make_environment_check_i_know_what_i_am_doing_true_should_set_environment_YES():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'check_i_know_what_i_am_doing': True})

    assert environment.get('BORG_CHECK_I_KNOW_WHAT_I_AM_DOING') == 'YES'


def test_make_environment_check_i_know_what_i_am_doing_false_should_set_environment_NO():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'check_i_know_what_i_am_doing': False})

    assert environment.get('BORG_CHECK_I_KNOW_WHAT_I_AM_DOING') == 'NO'


def test_make_environment_debug_passphrase_true_should_set_environment_YES():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'debug_passphrase': True})

    assert environment.get('BORG_DEBUG_PASSPHRASE') == 'YES'


def test_make_environment_debug_passphrase_false_should_set_environment_NO():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'debug_passphrase': False})

    assert environment.get('BORG_DEBUG_PASSPHRASE') == 'NO'


def test_make_environment_display_passphrase_true_should_set_environment_YES():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'display_passphrase': True})

    assert environment.get('BORG_DISPLAY_PASSPHRASE') == 'YES'


def test_make_environment_display_passphrase_false_should_set_environment_NO():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'display_passphrase': False})

    assert environment.get('BORG_DISPLAY_PASSPHRASE') == 'NO'


def test_make_environment_with_integer_variable_value():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()
    environment = module.make_environment({'borg_files_cache_ttl': 40})

    assert environment.get('BORG_FILES_CACHE_TTL') == '40'


def test_make_environment_with_use_chunks_archive_should_set_correct_environment_value():
    flexmock(module.os).should_receive('environ').and_return({'USER': 'root'})
    flexmock(module.borgmatic.hooks.credential.parse).should_receive(
        'resolve_credential'
    ).and_return(None)
    flexmock(module.os).should_receive('pipe').never()

    environment = module.make_environment({'use_chunks_archive': True})
    assert environment.get('BORG_USE_CHUNKS_ARCHIVE') == 'YES'

    environment = module.make_environment({'use_chunks_archive': False})
    assert environment.get('BORG_USE_CHUNKS_ARCHIVE') == 'NO'
