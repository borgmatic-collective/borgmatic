def repository_enabled_for_checks(repository, config):
    '''
    Given a repository name and a configuration dict, return whether the
    repository is enabled to have consistency checks run.
    '''
    if not config.get('check_repositories'):
        return True

    return repository in config['check_repositories']
