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


def make_environment(storage_config):
    '''
    Given a borgmatic storage configuration dict, return its options converted to a Borg environment
    variable dict.
    '''
    environment = {}

    for option_name, environment_variable_name in OPTION_TO_ENVIRONMENT_VARIABLE.items():
        value = storage_config.get(option_name)

        if value:
            environment[environment_variable_name] = value

    for (
        option_name,
        environment_variable_name,
    ) in DEFAULT_BOOL_OPTION_TO_ENVIRONMENT_VARIABLE.items():
        value = storage_config.get(option_name, False)
        environment[environment_variable_name] = 'yes' if value else 'no'

    return environment
