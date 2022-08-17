import logging


def normalize(config_filename, config):
    '''
    Given a configuration filename and a configuration dict of its loaded contents, apply particular
    hard-coded rules to normalize the configuration to adhere to the current schema. Return any log
    message warnings produced based on the normalization performed.
    '''
    logs = []

    # Upgrade exclude_if_present from a string to a list.
    exclude_if_present = config.get('location', {}).get('exclude_if_present')
    if isinstance(exclude_if_present, str):
        config['location']['exclude_if_present'] = [exclude_if_present]

    # Upgrade various monitoring hooks from a string to a dict.
    healthchecks = config.get('hooks', {}).get('healthchecks')
    if isinstance(healthchecks, str):
        config['hooks']['healthchecks'] = {'ping_url': healthchecks}

    cronitor = config.get('hooks', {}).get('cronitor')
    if isinstance(cronitor, str):
        config['hooks']['cronitor'] = {'ping_url': cronitor}

    pagerduty = config.get('hooks', {}).get('pagerduty')
    if isinstance(pagerduty, str):
        config['hooks']['pagerduty'] = {'integration_key': pagerduty}

    cronhub = config.get('hooks', {}).get('cronhub')
    if isinstance(cronhub, str):
        config['hooks']['cronhub'] = {'ping_url': cronhub}

    # Upgrade consistency checks from a list of strings to a list of dicts.
    checks = config.get('consistency', {}).get('checks')
    if isinstance(checks, list) and len(checks) and isinstance(checks[0], str):
        config['consistency']['checks'] = [{'name': check_type} for check_type in checks]

    # Upgrade remote repositories to ssh:// syntax, required in Borg 2.
    repositories = config.get('location', {}).get('repositories')
    if repositories:
        config['location']['repositories'] = []
        for repository in repositories:
            # TODO: Instead of logging directly here, return logs and bubble them up to be displayed *after* logging is initialized.
            if '~' in repository:
                logs.append(
                    logging.makeLogRecord(
                        dict(
                            levelno=logging.WARNING,
                            levelname='WARNING',
                            msg=f'{config_filename}: Repository paths containing "~" are deprecated in borgmatic and no longer work in Borg 2.',
                        )
                    )
                )
            if ':' in repository and not repository.startswith('ssh://'):
                rewritten_repository = (
                    f"ssh://{repository.replace(':~', '/~').replace(':/', '/').replace(':', '/./')}"
                )
                logs.append(
                    logging.makeLogRecord(
                        dict(
                            levelno=logging.WARNING,
                            levelname='WARNING',
                            msg=f'{config_filename}: Remote repository paths without ssh:// syntax are deprecated. Interpreting "{repository}" as "{rewritten_repository}"',
                        )
                    )
                )
                config['location']['repositories'].append(rewritten_repository)
            else:
                config['location']['repositories'].append(repository)

    return logs
