from flexmock import flexmock

from borgmatic.actions import dump as module


def test_dump_cleanup_removes_data_source_dumps():
    flexmock(module.borgmatic.hooks.dispatch).should_receive(
        'call_hooks_even_if_unconfigured'
    ).with_args('remove_data_source_dumps', object, object, object, object, object).twice()

    with module.Dump_cleanup(
        config=flexmock(),
        borgmatic_runtime_directory=flexmock(),
        patterns=flexmock(),
        dry_run=flexmock(),
    ):
        pass
