from io import StringIO

from collections import OrderedDict
import string

from borgmatic.config import legacy as module


def test_parse_section_options_with_punctuation_should_return_section_options():
    parser = module.RawConfigParser()
    parser.read_file(StringIO('[section]\nfoo: {}\n'.format(string.punctuation)))

    section_format = module.Section_format(
        'section', (module.Config_option('foo', str, required=True),)
    )

    config = module.parse_section_options(parser, section_format)

    assert config == OrderedDict((('foo', string.punctuation),))
