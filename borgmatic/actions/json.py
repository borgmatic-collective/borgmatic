import json


def parse_json(borg_json_output, label):
    '''
    Given a Borg JSON output string, parse it as JSON into a dict. Inject the given borgmatic
    repository label into it and return the dict.
    '''
    json_data = json.loads(borg_json_output)

    if 'repository' not in json_data:
        return json_data

    json_data['repository']['label'] = label or ''

    return json_data
