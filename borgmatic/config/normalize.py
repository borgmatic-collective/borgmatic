import logging
import os


def normalize_sections(config_filename, config):
    '''
    Given a configuration filename and a configuration dict of its loaded contents, airlift any
    options out of sections ("location:", etc.) to the global scope and delete those sections.
    Return any log message warnings produced based on the normalization performed.

    Raise ValueError if the "prefix" option is set in both "location" and "consistency" sections.
    '''
    try:
        location = config.get('location') or {}
    except AttributeError:
        raise ValueError('Configuration does not contain any options')

    storage = config.get('storage') or {}
    consistency = config.get('consistency') or {}
    hooks = config.get('hooks') or {}

    if (
        location.get('prefix')
        and consistency.get('prefix')
        and location.get('prefix') != consistency.get('prefix')
    ):
        raise ValueError(
            'The retention prefix and the consistency prefix cannot have different values (unless one is not set).'
        )

    if storage.get('umask') and hooks.get('umask') and storage.get('umask') != hooks.get('umask'):
        raise ValueError(
            'The storage umask and the hooks umask cannot have different values (unless one is not set).'
        )

    any_section_upgraded = False

    # Move any options from deprecated sections into the global scope.
    for section_name in ('location', 'storage', 'retention', 'consistency', 'output', 'hooks'):
        section_config = config.get(section_name)

        if section_config is not None:
            any_section_upgraded = True
            del config[section_name]
            config.update(section_config)

    if any_section_upgraded:
        return [
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: Configuration sections (like location:, storage:, retention:, consistency:, and hooks:) are deprecated and support will be removed from a future release. To prepare for this, move your options out of sections to the global scope.',
                )
            )
        ]

    return []


def make_command_hook_deprecation_log(config_filename, option_name):  # pragma: no cover
    '''
    Given a configuration filename and the name of a configuration option, return a deprecation
    warning log for it.
    '''
    return logging.makeLogRecord(
        dict(
            levelno=logging.WARNING,
            levelname='WARNING',
            msg=f'{config_filename}: {option_name} is deprecated and support will be removed from a future release. Use commands: instead.',
        )
    )


def normalize_commands(config_filename, config):
    '''
    Given a configuration filename and a configuration dict, transform any "before_*"- and
    "after_*"-style command hooks into "commands:".
    '''
    logs = []

    # Normalize "before_actions" and "after_actions".
    for preposition in ('before', 'after'):
        option_name = f'{preposition}_actions'
        commands = config.pop(option_name, None)

        if commands:
            logs.append(make_command_hook_deprecation_log(config_filename, option_name))
            config.setdefault('commands', []).append(
                {
                    preposition: 'repository',
                    'run': commands,
                }
            )

    # Normalize "before_backup", "before_prune", "after_backup", "after_prune", etc.
    for action_name in ('create', 'prune', 'compact', 'check', 'extract'):
        for preposition in ('before', 'after'):
            option_name = f'{preposition}_{"backup" if action_name == "create" else action_name}'
            commands = config.pop(option_name, None)

            if not commands:
                continue

            logs.append(make_command_hook_deprecation_log(config_filename, option_name))
            config.setdefault('commands', []).append(
                {
                    preposition: 'action',
                    'when': [action_name],
                    'run': commands,
                }
            )

    # Normalize "on_error".
    commands = config.pop('on_error', None)

    if commands:
        logs.append(make_command_hook_deprecation_log(config_filename, 'on_error'))
        config.setdefault('commands', []).append(
            {
                'after': 'error',
                'when': ['create', 'prune', 'compact', 'check'],
                'run': commands,
            }
        )

    # Normalize "before_everything" and "after_everything".
    for preposition in ('before', 'after'):
        option_name = f'{preposition}_everything'
        commands = config.pop(option_name, None)

        if commands:
            logs.append(make_command_hook_deprecation_log(config_filename, option_name))
            config.setdefault('commands', []).append(
                {
                    preposition: 'everything',
                    'when': ['create'],
                    'run': commands,
                }
            )

    return logs


def normalize(config_filename, config):
    '''
    Given a configuration filename and a configuration dict of its loaded contents, apply particular
    hard-coded rules to normalize the configuration to adhere to the current schema. Return any log
    message warnings produced based on the normalization performed.

    Raise ValueError the configuration cannot be normalized.
    '''
    logs = normalize_sections(config_filename, config)
    logs += normalize_commands(config_filename, config)

    if config.get('borgmatic_source_directory'):
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The borgmatic_source_directory option is deprecated and will be removed from a future release. Use user_runtime_directory and user_state_directory instead.',
                )
            )
        )

    # Upgrade exclude_if_present from a string to a list.
    exclude_if_present = config.get('exclude_if_present')
    if isinstance(exclude_if_present, str):
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The exclude_if_present option now expects a list value. String values for this option are deprecated and support will be removed from a future release.',
                )
            )
        )
        config['exclude_if_present'] = [exclude_if_present]

    # Unconditionally set the bootstrap hook so that it's enabled by default and config files get
    # stored in each Borg archive.
    config.setdefault('bootstrap', {})

    # Move store_config_files from the global scope to the bootstrap hook.
    store_config_files = config.get('store_config_files')
    if store_config_files is not None:
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The store_config_files option has moved under the bootstrap hook. Specifying store_config_files at the global scope is deprecated and support will be removed from a future release.',
                )
            )
        )
        del config['store_config_files']
        config['bootstrap']['store_config_files'] = store_config_files

    # Upgrade various monitoring hooks from a string to a dict.
    healthchecks = config.get('healthchecks')
    if isinstance(healthchecks, str):
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The healthchecks hook now expects a key/value pair with "ping_url" as a key. String values for this option are deprecated and support will be removed from a future release.',
                )
            )
        )
        config['healthchecks'] = {'ping_url': healthchecks}

    cronitor = config.get('cronitor')
    if isinstance(cronitor, str):
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The healthchecks hook now expects key/value pairs. String values for this option are deprecated and support will be removed from a future release.',
                )
            )
        )
        config['cronitor'] = {'ping_url': cronitor}

    pagerduty = config.get('pagerduty')
    if isinstance(pagerduty, str):
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The healthchecks hook now expects key/value pairs. String values for this option are deprecated and support will be removed from a future release.',
                )
            )
        )
        config['pagerduty'] = {'integration_key': pagerduty}

    cronhub = config.get('cronhub')
    if isinstance(cronhub, str):
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The healthchecks hook now expects key/value pairs. String values for this option are deprecated and support will be removed from a future release.',
                )
            )
        )
        config['cronhub'] = {'ping_url': cronhub}

    # Upgrade consistency checks from a list of strings to a list of dicts.
    checks = config.get('checks')
    if isinstance(checks, list) and len(checks) and isinstance(checks[0], str):
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The checks option now expects a list of key/value pairs. Lists of strings for this option are deprecated and support will be removed from a future release.',
                )
            )
        )
        config['checks'] = [{'name': check_type} for check_type in checks]

    # Rename various configuration options.
    numeric_owner = config.pop('numeric_owner', None)
    if numeric_owner is not None:
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The numeric_owner option has been renamed to numeric_ids. numeric_owner is deprecated and support will be removed from a future release.',
                )
            )
        )
        config['numeric_ids'] = numeric_owner

    bsd_flags = config.pop('bsd_flags', None)
    if bsd_flags is not None:
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The bsd_flags option has been renamed to flags. bsd_flags is deprecated and support will be removed from a future release.',
                )
            )
        )
        config['flags'] = bsd_flags

    remote_rate_limit = config.pop('remote_rate_limit', None)
    if remote_rate_limit is not None:
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The remote_rate_limit option has been renamed to upload_rate_limit. remote_rate_limit is deprecated and support will be removed from a future release.',
                )
            )
        )
        config['upload_rate_limit'] = remote_rate_limit

    # Upgrade remote repositories to ssh:// syntax, required in Borg 2.
    repositories = config.get('repositories')
    if repositories:
        if any(isinstance(repository, str) for repository in repositories):
            logs.append(
                logging.makeLogRecord(
                    dict(
                        levelno=logging.WARNING,
                        levelname='WARNING',
                        msg=f'{config_filename}: The repositories option now expects a list of key/value pairs. Lists of strings for this option are deprecated and support will be removed from a future release.',
                    )
                )
            )
            config['repositories'] = [
                {'path': repository} if isinstance(repository, str) else repository
                for repository in repositories
            ]
            repositories = config['repositories']

        config['repositories'] = []

        for repository_dict in repositories:
            repository_path = repository_dict.get('path')

            if repository_path is None:
                continue

            if '~' in repository_path:
                logs.append(
                    logging.makeLogRecord(
                        dict(
                            levelno=logging.WARNING,
                            levelname='WARNING',
                            msg=f'{config_filename}: Repository paths containing "~" are deprecated in borgmatic and support will be removed from a future release.',
                        )
                    )
                )
            if ':' in repository_path:
                if repository_path.startswith('file://'):
                    updated_repository_path = os.path.abspath(
                        repository_path.partition('file://')[-1]
                    )
                    config['repositories'].append(
                        dict(
                            repository_dict,
                            path=updated_repository_path,
                        )
                    )
                elif (
                    repository_path.startswith('ssh://')
                    or repository_path.startswith('sftp://')
                    or repository_path.startswith('rclone:')
                    or repository_path.startswith('s3:')
                    or repository_path.startswith('b2:')
                ):
                    config['repositories'].append(repository_dict)
                else:
                    rewritten_repository_path = f"ssh://{repository_path.replace(':~', '/~').replace(':/', '/').replace(':', '/./')}"
                    logs.append(
                        logging.makeLogRecord(
                            dict(
                                levelno=logging.WARNING,
                                levelname='WARNING',
                                msg=f'{config_filename}: Remote repository paths without ssh://, sftp://, rclone:, s3:, or b2:, syntax are deprecated and support will be removed from a future release. Interpreting "{repository_path}" as "{rewritten_repository_path}"',
                            )
                        )
                    )
                    config['repositories'].append(
                        dict(
                            repository_dict,
                            path=rewritten_repository_path,
                        )
                    )
            else:
                config['repositories'].append(repository_dict)

    if config.get('prefix'):
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The prefix option is deprecated and support will be removed from a future release. Use archive_name_format or match_archives instead.',
                )
            )
        )

    return logs
