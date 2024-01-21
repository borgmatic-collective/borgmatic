from borgmatic.borg import environment as module


def test_make_environment_with_passcommand_should_set_environment():
    environment = module.make_environment({'encryption_passcommand': 'command'})

    assert environment.get('BORG_PASSCOMMAND') == 'command'


def test_make_environment_with_passphrase_should_set_environment():
    environment = module.make_environment({'encryption_passphrase': 'pass'})

    assert environment.get('BORG_PASSPHRASE') == 'pass'


def test_make_environment_with_ssh_command_should_set_environment():
    environment = module.make_environment({'ssh_command': 'ssh -C'})

    assert environment.get('BORG_RSH') == 'ssh -C'


def test_make_environment_without_configuration_should_not_set_environment():
    environment = module.make_environment({})

    # borgmatic always sets this Borg environment variable.
    assert environment == {'BORG_EXIT_CODES': 'modern'}


def test_make_environment_with_relocated_repo_access_true_should_set_environment_yes():
    environment = module.make_environment({'relocated_repo_access_is_ok': True})

    assert environment.get('BORG_RELOCATED_REPO_ACCESS_IS_OK') == 'yes'


def test_make_environment_with_relocated_repo_access_false_should_set_environment_no():
    environment = module.make_environment({'relocated_repo_access_is_ok': False})

    assert environment.get('BORG_RELOCATED_REPO_ACCESS_IS_OK') == 'no'


def test_make_environment_check_i_know_what_i_am_doing_true_should_set_environment_YES():
    environment = module.make_environment({'check_i_know_what_i_am_doing': True})

    assert environment.get('BORG_CHECK_I_KNOW_WHAT_I_AM_DOING') == 'YES'


def test_make_environment_check_i_know_what_i_am_doing_false_should_set_environment_NO():
    environment = module.make_environment({'check_i_know_what_i_am_doing': False})

    assert environment.get('BORG_CHECK_I_KNOW_WHAT_I_AM_DOING') == 'NO'


def test_make_environment_with_integer_variable_value():
    environment = module.make_environment({'borg_files_cache_ttl': 40})
    assert environment.get('BORG_FILES_CACHE_TTL') == '40'
