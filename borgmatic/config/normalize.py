def normalize(config):
    '''
    Given a configuration dict, apply particular hard-coded rules to normalize its contents to
    adhere to the configuration schema.
    '''
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
