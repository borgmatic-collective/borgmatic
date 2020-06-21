import os

from borgmatic.borg import environment as module


def test_initialize_with_passcommand_should_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({'encryption_passcommand': 'command'})
        assert os.environ.get('BORG_PASSCOMMAND') == 'command'
    finally:
        os.environ = orig_environ


def test_initialize_with_passphrase_should_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({'encryption_passphrase': 'pass'})
        assert os.environ.get('BORG_PASSPHRASE') == 'pass'
    finally:
        os.environ = orig_environ


def test_initialize_with_ssh_command_should_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({'ssh_command': 'ssh -C'})
        assert os.environ.get('BORG_RSH') == 'ssh -C'
    finally:
        os.environ = orig_environ


def test_initialize_without_configuration_should_only_set_default_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({})

        assert {key: value for key, value in os.environ.items() if key.startswith('BORG_')} == {
            'BORG_RELOCATED_REPO_ACCESS_IS_OK': 'no',
            'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK': 'no',
        }
    finally:
        os.environ = orig_environ


def test_initialize_with_relocated_repo_access_should_override_default():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({'relocated_repo_access_is_ok': True})
        assert os.environ.get('BORG_RELOCATED_REPO_ACCESS_IS_OK') == 'yes'
    finally:
        os.environ = orig_environ


def test_initialize_prefers_configuration_option_over_borg_environment_variable():
    orig_environ = os.environ

    try:
        os.environ = {'BORG_SSH': 'mosh'}
        module.initialize({'ssh_command': 'ssh -C'})
        assert os.environ.get('BORG_RSH') == 'ssh -C'
    finally:
        os.environ = orig_environ


def test_initialize_passes_through_existing_borg_environment_variable():
    orig_environ = os.environ

    try:
        os.environ = {'BORG_PASSPHRASE': 'pass'}
        module.initialize({'ssh_command': 'ssh -C'})
        assert os.environ.get('BORG_PASSPHRASE') == 'pass'
    finally:
        os.environ = orig_environ
