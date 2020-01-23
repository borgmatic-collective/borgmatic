def normalize(config):
    '''
    Given a configuration dict, apply particular hard-coded rules to normalize its contents to
    adhere to the configuration schema.
    '''
    exclude_if_present = config.get('location', {}).get('exclude_if_present')

    # "Upgrade" exclude_if_present from a string to a list.
    if isinstance(exclude_if_present, str):
        config['location']['exclude_if_present'] = [exclude_if_present]
