OPTION_TO_ENVIRONMENT_VARIABLE = {
    'borg_base_directory': 'BORG_BASE_DIR',
    'borg_config_directory': 'BORG_CONFIG_DIR',
    'borg_cache_directory': 'BORG_CACHE_DIR',
    'borg_files_cache_ttl': 'BORG_FILES_CACHE_TTL',
    'borg_security_directory': 'BORG_SECURITY_DIR',
    'borg_keys_directory': 'BORG_KEYS_DIR',
    'encryption_passcommand': 'BORG_PASSCOMMAND',
    'encryption_passphrase': 'BORG_PASSPHRASE',
    'ssh_command': 'BORG_RSH',
    'temporary_directory': 'TMPDIR',
}

DEFAULT_BOOL_OPTION_TO_DOWNCASE_ENVIRONMENT_VARIABLE = {
    'relocated_repo_access_is_ok': 'BORG_RELOCATED_REPO_ACCESS_IS_OK',
    'unknown_unencrypted_repo_access_is_ok': 'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK',
}

DEFAULT_BOOL_OPTION_TO_UPPERCASE_ENVIRONMENT_VARIABLE = {
    'check_i_know_what_i_am_doing': 'BORG_CHECK_I_KNOW_WHAT_I_AM_DOING',
}


def make_environment(config):
    '''
    Given a borgmatic configuration dict, return its options converted to a Borg environment
    variable dict.
    '''
    environment = {}

    for option_name, environment_variable_name in OPTION_TO_ENVIRONMENT_VARIABLE.items():
        value = config.get(option_name)

        if value:
            environment[environment_variable_name] = str(value)

    for (
        option_name,
        environment_variable_name,
    ) in DEFAULT_BOOL_OPTION_TO_DOWNCASE_ENVIRONMENT_VARIABLE.items():
        value = config.get(option_name)
        environment[environment_variable_name] = 'yes' if value else 'no'

    for (
        option_name,
        environment_variable_name,
    ) in DEFAULT_BOOL_OPTION_TO_UPPERCASE_ENVIRONMENT_VARIABLE.items():
        value = config.get(option_name)
        if value is not None:
            environment[environment_variable_name] = 'YES' if value else 'NO'

    # On Borg 1.4.0a1+, take advantage of more specific exit codes. No effect on
    # older versions of Borg.
    environment['BORG_EXIT_CODES'] = 'modern'

    return environment
