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


def test_make_environment_without_configuration_should_only_set_default_environment():
    environment = module.make_environment({})

    assert environment == {
        'BORG_RELOCATED_REPO_ACCESS_IS_OK': 'no',
        'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK': 'no',
    }


def test_make_environment_with_relocated_repo_access_should_override_default():
    environment = module.make_environment({'relocated_repo_access_is_ok': True})

    assert environment.get('BORG_RELOCATED_REPO_ACCESS_IS_OK') == 'yes'
