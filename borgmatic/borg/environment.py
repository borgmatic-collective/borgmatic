import os

import borgmatic.borg.passcommand
import borgmatic.hooks.credential.parse

OPTION_TO_ENVIRONMENT_VARIABLE = {
    'borg_base_directory': 'BORG_BASE_DIR',
    'borg_config_directory': 'BORG_CONFIG_DIR',
    'borg_cache_directory': 'BORG_CACHE_DIR',
    'borg_files_cache_ttl': 'BORG_FILES_CACHE_TTL',
    'borg_security_directory': 'BORG_SECURITY_DIR',
    'borg_keys_directory': 'BORG_KEYS_DIR',
    'encryption_passphrase': 'BORG_PASSPHRASE',
    'ssh_command': 'BORG_RSH',
    'temporary_directory': 'TMPDIR',
}

CREDENTIAL_OPTIONS = {'encryption_passphrase'}

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

    Do not reuse this environment across multiple Borg invocations, because it can include
    references to resources like anonymous pipes for passphrases—which can only be consumed once.
    '''
    environment = {}

    for option_name, environment_variable_name in OPTION_TO_ENVIRONMENT_VARIABLE.items():
        value = config.get(option_name)

        if option_name in CREDENTIAL_OPTIONS and value is not None:
            value = borgmatic.hooks.credential.parse.resolve_credential(value, config)

        if value is not None:
            environment[environment_variable_name] = str(value)

    passphrase = borgmatic.borg.passcommand.get_passphrase_from_passcommand(config)

    # If the passcommand produced a passphrase, send it to Borg via an anonymous pipe.
    if passphrase:
        read_file_descriptor, write_file_descriptor = os.pipe()
        os.write(write_file_descriptor, passphrase.encode('utf-8'))
        os.close(write_file_descriptor)

        # This, plus subprocess.Popen(..., close_fds=False) in execute.py, is necessary for the Borg
        # child process to inherit the file descriptor.
        os.set_inheritable(read_file_descriptor, True)
        environment['BORG_PASSPHRASE_FD'] = str(read_file_descriptor)

    for (
        option_name,
        environment_variable_name,
    ) in DEFAULT_BOOL_OPTION_TO_DOWNCASE_ENVIRONMENT_VARIABLE.items():
        if os.environ.get(environment_variable_name) is None:
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
