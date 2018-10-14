def repository_enabled_for_checks(repository, consistency):
    '''
    Given a repository name and a consistency configuration dict, return whether the repository
    is enabled to have consistency checks run.
    '''
    if not consistency.get('check_repositories'):
        return True

    return repository in consistency['check_repositories']
