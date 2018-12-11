import os


def initialize(storage_config):
    passcommand = storage_config.get('encryption_passcommand')
    if passcommand:
        os.environ['BORG_PASSCOMMAND'] = passcommand

    passphrase = storage_config.get('encryption_passphrase')
    if passphrase:
        os.environ['BORG_PASSPHRASE'] = passphrase

    ssh_command = storage_config.get('ssh_command')
    if ssh_command:
        os.environ['BORG_RSH'] = ssh_command
