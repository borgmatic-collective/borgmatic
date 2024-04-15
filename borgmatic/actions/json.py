import json
import logging

logger = logging.getLogger(__name__)


def parse_json(borg_json_output, label):
    '''
    Given a Borg JSON output string, parse it as JSON into a dict. Inject the given borgmatic
    repository label into it and return the dict.

    Raise JSONDecodeError if the JSON output cannot be parsed.
    '''
    lines = borg_json_output.splitlines()
    start_line_index = 0

    # Scan forward to find the first line starting with "{" and assume that's where the JSON starts.
    for line_index, line in enumerate(lines):
        if line.startswith('{'):
            start_line_index = line_index
            break

    json_data = json.loads('\n'.join(lines[start_line_index:]))

    if 'repository' not in json_data:
        return json_data

    json_data['repository']['label'] = label or ''

    return json_data
