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
    'temporary_directory': 'TMPDIR',
}

DEFAULT_BOOL_OPTION_TO_ENVIRONMENT_VARIABLE = {
    'relocated_repo_access_is_ok': 'BORG_RELOCATED_REPO_ACCESS_IS_OK',
    'unknown_unencrypted_repo_access_is_ok': 'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK',
}


def initialize(storage_config):
    for option_name, environment_variable_name in OPTION_TO_ENVIRONMENT_VARIABLE.items():

        # Options from borgmatic configuration take precedence over already set BORG_* environment
        # variables.
        value = storage_config.get(option_name) or os.environ.get(environment_variable_name)

        if value:
            os.environ[environment_variable_name] = value
        else:
            os.environ.pop(environment_variable_name, None)

    for (
        option_name,
        environment_variable_name,
    ) in DEFAULT_BOOL_OPTION_TO_ENVIRONMENT_VARIABLE.items():
        value = storage_config.get(option_name, False)
        os.environ[environment_variable_name] = 'yes' if value else 'no'
