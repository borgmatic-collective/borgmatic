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


def test_initialize_without_configuration_should_not_set_environment():
    orig_environ = os.environ

    try:
        os.environ = {}
        module.initialize({})
        assert os.environ.get('BORG_PASSCOMMAND') is None
        assert os.environ.get('BORG_PASSPHRASE') is None
        assert os.environ.get('BORG_RSH') is None
    finally:
        os.environ = orig_environ
