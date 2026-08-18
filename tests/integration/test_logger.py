from flexmock import flexmock

import borgmatic.logger as module


def test_json_formatter_format_does_not_raise():
    module.Json_formatter().format(
        flexmock(
            created=12345,
            levelno=module.logging.INFO,
            levelname='INFO',
            name='borg.something',
            getMessage=lambda: 'All done',
        )
    )
