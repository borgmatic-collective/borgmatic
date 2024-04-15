import pytest

from borgmatic.actions import json as module


def test_parse_json_loads_json_from_string():
    assert module.parse_json('{"repository": {"id": "foo"}}', label=None) == {
        'repository': {'id': 'foo', 'label': ''}
    }


def test_parse_json_skips_non_json_warnings_and_loads_subsequent_json():
    assert module.parse_json(
        '/non/existent/path: stat: [Errno 2] No such file or directory: /non/existent/path\n{"repository":\n{"id": "foo"}}',
        label=None,
    ) == {'repository': {'id': 'foo', 'label': ''}}


def test_parse_json_skips_with_invalid_json_raises():
    with pytest.raises(module.json.JSONDecodeError):
        module.parse_json('this is not valid JSON }', label=None)


def test_parse_json_injects_label_into_parsed_data():
    assert module.parse_json('{"repository": {"id": "foo"}}', label='bar') == {
        'repository': {'id': 'foo', 'label': 'bar'}
    }


def test_parse_json_injects_nothing_when_repository_missing():
    assert module.parse_json('{"stuff": {"id": "foo"}}', label='bar') == {'stuff': {'id': 'foo'}}
