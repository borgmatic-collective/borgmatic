from flexmock import flexmock

from borgmatic.actions import json as module


def test_parse_json_loads_json_from_string():
    flexmock(module.json).should_receive('loads').and_return({'repository': {'id': 'foo'}})

    assert module.parse_json('{"repository": {"id": "foo"}}', label=None) == {
        'repository': {'id': 'foo', 'label': ''}
    }


def test_parse_json_injects_label_into_parsed_data():
    flexmock(module.json).should_receive('loads').and_return({'repository': {'id': 'foo'}})

    assert module.parse_json('{"repository": {"id": "foo"}}', label='bar') == {
        'repository': {'id': 'foo', 'label': 'bar'}
    }


def test_parse_json_injects_nothing_when_repository_missing():
    flexmock(module.json).should_receive('loads').and_return({'stuff': {'id': 'foo'}})

    assert module.parse_json('{"stuff": {"id": "foo"}}', label='bar') == {'stuff': {'id': 'foo'}}
