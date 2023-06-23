from flexmock import flexmock

from borgmatic.actions.config import validate as module


def test_run_validate_does_not_raise():
    validate_arguments = flexmock(show=False)
    flexmock(module.borgmatic.config.generate).should_receive('render_configuration')

    module.run_validate(validate_arguments, flexmock())


def test_run_validate_with_show_does_not_raise():
    validate_arguments = flexmock(show=True)
    flexmock(module.borgmatic.config.generate).should_receive('render_configuration')

    module.run_validate(validate_arguments, {'test.yaml': flexmock(), 'other.yaml': flexmock()})
