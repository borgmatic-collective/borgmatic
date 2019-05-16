import os

OPTION_TO_ENVIRONMENT_VARIABLE = {
    'borg_base_directory': 'BORG_BASE_DIR',
    'borg_config_directory': 'BORG_CONFIG_DIR',
    'borg_cache_directory': 'BORG_CACHE_DIR',
    'borg_security_directory': 'BORG_SECURITY_DIR',
    'borg_keys_directory': 'BORG_KEYS_DIR',
    'encryption_passcommand': 'BORG_PASSCOMMAND',
    'encryption_passphrase': 'BORG_PASSPHRASE',
    'ssh_command': 'BORG_RSH',
}


def initialize(storage_config):
    for option_name, environment_variable_name in OPTION_TO_ENVIRONMENT_VARIABLE.items():
        value = storage_config.get(option_name)
        if value:
            os.environ[environment_variable_name] = value
