from flexmock import flexmock

from borgmatic.actions.config import generate as module


def test_run_generate_does_not_raise():
    generate_arguments = flexmock(
        source_filename=None,
        destination_filename='destination.yaml',
        overwrite=False,
    )
    global_arguments = flexmock(dry_run=False)
    flexmock(module.borgmatic.config.generate).should_receive('generate_sample_configuration')

    module.run_generate(generate_arguments, global_arguments)


def test_run_generate_with_dry_run_does_not_raise():
    generate_arguments = flexmock(
        source_filename=None,
        destination_filename='destination.yaml',
        overwrite=False,
    )
    global_arguments = flexmock(dry_run=True)
    flexmock(module.borgmatic.config.generate).should_receive('generate_sample_configuration')

    module.run_generate(generate_arguments, global_arguments)


def test_run_generate_with_source_filename_does_not_raise():
    generate_arguments = flexmock(
        source_filename='source.yaml',
        destination_filename='destination.yaml',
        overwrite=False,
    )
    global_arguments = flexmock(dry_run=False)
    flexmock(module.borgmatic.config.generate).should_receive('generate_sample_configuration')

    module.run_generate(generate_arguments, global_arguments)
