from borgmatic.borg import feature as module


def test_available_true_for_new_enough_borg_version():
    assert module.available(module.Feature.COMPACT, '1.3.7')


def test_available_true_for_borg_version_introducing_feature():
    assert module.available(module.Feature.COMPACT, '1.2.0a2')


def test_available_true_for_borg_stable_version_introducing_feature():
    assert module.available(module.Feature.COMPACT, '1.2.0')


def test_available_false_for_too_old_borg_version():
    assert not module.available(module.Feature.COMPACT, '1.1.5')
