from borgmatic.actions import arguments as module


def test_update_arguments_copies_and_updates_without_modifying_original():
    original = module.argparse.Namespace(foo=1, bar=2, baz=3)

    result = module.update_arguments(original, bar=7, baz=8)

    assert original == module.argparse.Namespace(foo=1, bar=2, baz=3)
    assert result == module.argparse.Namespace(foo=1, bar=7, baz=8)
