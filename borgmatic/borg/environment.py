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
    'ssh_command': 'BORG_RSH',
    'temporary_directory': 'TMPDIR',
}

DEFAULT_BOOL_OPTION_TO_UNCONDITIONAL_ENVIRONMENT_VARIABLE = {
    'check_i_know_what_i_am_doing': 'BORG_CHECK_I_KNOW_WHAT_I_AM_DOING',
}

DEFAULT_BOOL_OPTION_TO_ENVIRONMENT_VARIABLE = {
    'debug_passphrase': 'BORG_DEBUG_PASSPHRASE',
    'display_passphrase': 'BORG_DISPLAY_PASSPHRASE',
    'relocated_repo_access_is_ok': 'BORG_RELOCATED_REPO_ACCESS_IS_OK',
    'unknown_unencrypted_repo_access_is_ok': 'BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK',
    'use_chunks_archive': 'BORG_USE_CHUNKS_ARCHIVE',
}


def make_environment(config):
    '''
    Given a borgmatic configuration dict, convert it to a Borg environment variable dict, merge it
    with a copy of the current environment variables, and return the result.

    Do not reuse this environment across multiple Borg invocations, because it can include
    references to resources like anonymous pipes for passphrases—which can only be consumed once.

    Here's how native Borg precedence works for a few of the environment variables:

      1. BORG_PASSPHRASE, if set, is used first.
      2. BORG_PASSCOMMAND is used only if BORG_PASSPHRASE isn't set.
      3. BORG_PASSPHRASE_FD is used only if neither of the above are set.

    In borgmatic, we want to simulate this precedence order, but there are some additional
    complications. First, values can come from either configuration or from environment variables
    set outside borgmatic; configured options should take precedence. Second, when borgmatic gets a
    passphrase—directly from configuration or indirectly via a credential hook or a passcommand—we
    want to pass that passphrase to Borg via an anonymous pipe (+ BORG_PASSPHRASE_FD), since that's
    more secure than using an environment variable (BORG_PASSPHRASE).
    '''
    environment = dict(os.environ)

    for option_name, environment_variable_name in OPTION_TO_ENVIRONMENT_VARIABLE.items():
        value = config.get(option_name)

        if value is not None:
            environment[environment_variable_name] = str(value)

    if 'encryption_passphrase' in config:
        environment.pop('BORG_PASSPHRASE', None)
        environment.pop('BORG_PASSCOMMAND', None)

    if 'encryption_passcommand' in config:
        environment.pop('BORG_PASSCOMMAND', None)

    passphrase = borgmatic.hooks.credential.parse.resolve_credential(
        config.get('encryption_passphrase'), config
    )

    if passphrase is None:
        passphrase = borgmatic.borg.passcommand.get_passphrase_from_passcommand(config)

    # If there's a passphrase (from configuration, from a configured credential, or from a
    # configured passcommand), send it to Borg via an anonymous pipe.
    if passphrase is not None:
        read_file_descriptor, write_file_descriptor = os.pipe()
        os.write(write_file_descriptor, passphrase.encode('utf-8'))
        os.close(write_file_descriptor)

        # This plus subprocess.Popen(..., close_fds=False) in execute.py is necessary for the Borg
        # child process to inherit the file descriptor.
        os.set_inheritable(read_file_descriptor, True)
        environment['BORG_PASSPHRASE_FD'] = str(read_file_descriptor)

    for (
        option_name,
        environment_variable_name,
    ) in DEFAULT_BOOL_OPTION_TO_ENVIRONMENT_VARIABLE.items():
        if os.environ.get(environment_variable_name) is None:
            value = config.get(option_name)
            environment[environment_variable_name] = 'YES' if value else 'NO'

    for (
        option_name,
        environment_variable_name,
    ) in DEFAULT_BOOL_OPTION_TO_UNCONDITIONAL_ENVIRONMENT_VARIABLE.items():
        value = config.get(option_name)
        if value is not None:
            environment[environment_variable_name] = 'YES' if value else 'NO'

    # On Borg 1.4.0a1+, take advantage of more specific exit codes. No effect on
    # older versions of Borg.
    environment['BORG_EXIT_CODES'] = 'modern'

    return environment
