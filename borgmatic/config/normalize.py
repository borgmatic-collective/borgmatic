import logging
import os


def normalize(config_filename, config):
    '''
    Given a configuration filename and a configuration dict of its loaded contents, apply particular
    hard-coded rules to normalize the configuration to adhere to the current schema. Return any log
    message warnings produced based on the normalization performed.
    '''
    logs = []
    location = config.get('location') or {}
    storage = config.get('storage') or {}
    consistency = config.get('consistency') or {}
    retention = config.get('retention') or {}
    hooks = config.get('hooks') or {}

    # Upgrade exclude_if_present from a string to a list.
    exclude_if_present = location.get('exclude_if_present')
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
        config['location']['exclude_if_present'] = [exclude_if_present]

    # Upgrade various monitoring hooks from a string to a dict.
    healthchecks = hooks.get('healthchecks')
    if isinstance(healthchecks, str):
        logs.append(
            logging.makeLogRecord(
                dict(
                    levelno=logging.WARNING,
                    levelname='WARNING',
                    msg=f'{config_filename}: The healthchecks hook now expects a mapping value. String values for this option are deprecated and support will be removed from a future release.',
                )
            )
        )
        config['hooks']['healthchecks'] = {'ping_url': healthchecks}

    cronitor = hooks.get('cronitor')
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
        config['hooks']['cronitor'] = {'ping_url': cronitor}

    pagerduty = hooks.get('pagerduty')
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
        config['hooks']['pagerduty'] = {'integration_key': pagerduty}

    cronhub = hooks.get('cronhub')
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
        config['hooks']['cronhub'] = {'ping_url': cronhub}

    # Upgrade consistency checks from a list of strings to a list of dicts.
    checks = consistency.get('checks')
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
        config['consistency']['checks'] = [{'name': check_type} for check_type in checks]

    # Rename various configuration options.
    numeric_owner = location.pop('numeric_owner', None)
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
        config['location']['numeric_ids'] = numeric_owner

    bsd_flags = location.pop('bsd_flags', None)
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
        config['location']['flags'] = bsd_flags

    remote_rate_limit = storage.pop('remote_rate_limit', None)
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
        config['storage']['upload_rate_limit'] = remote_rate_limit

    # Upgrade remote repositories to ssh:// syntax, required in Borg 2.
    repositories = location.get('repositories')
    if repositories:
        if isinstance(repositories[0], str):
            logs.append(
                logging.makeLogRecord(
                    dict(
                        levelno=logging.WARNING,
                        levelname='WARNING',
                        msg=f'{config_filename}: The repositories option now expects a list of key/value pairs. Lists of strings for this option are deprecated and support will be removed from a future release.',
                    )
                )
            )
            config['location']['repositories'] = [
                {'path': repository} for repository in repositories
            ]
            repositories = config['location']['repositories']
        config['location']['repositories'] = []
        for repository_dict in repositories:
            repository_path = repository_dict['path']
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
                    config['location']['repositories'].append(
                        dict(
                            repository_dict,
                            path=updated_repository_path,
                        )
                    )
                elif repository_path.startswith('ssh://'):
                    config['location']['repositories'].append(repository_dict)
                else:
                    rewritten_repository_path = f"ssh://{repository_path.replace(':~', '/~').replace(':/', '/').replace(':', '/./')}"
                    logs.append(
                        logging.makeLogRecord(
                            dict(
                                levelno=logging.WARNING,
                                levelname='WARNING',
                                msg=f'{config_filename}: Remote repository paths without ssh:// syntax are deprecated and support will be removed from a future release. Interpreting "{repository_path}" as "{rewritten_repository_path}"',
                            )
                        )
                    )
                    config['location']['repositories'].append(
                        dict(
                            repository_dict,
                            path=rewritten_repository_path,
                        )
                    )
            else:
                config['location']['repositories'].append(repository_dict)

    if consistency.get('prefix') or retention.get('prefix'):
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
