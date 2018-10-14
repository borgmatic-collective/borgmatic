from borgmatic.config import checks as module


def test_repository_enabled_for_checks_defaults_to_enabled_for_all_repositories():
    enabled = module.repository_enabled_for_checks('repo.borg', consistency={})

    assert enabled


def test_repository_enabled_for_checks_is_enabled_for_specified_repositories():
    enabled = module.repository_enabled_for_checks(
        'repo.borg', consistency={'check_repositories': ['repo.borg', 'other.borg']}
    )

    assert enabled


def test_repository_enabled_for_checks_is_disabled_for_other_repositories():
    enabled = module.repository_enabled_for_checks(
        'repo.borg', consistency={'check_repositories': ['other.borg']}
    )

    assert not enabled
