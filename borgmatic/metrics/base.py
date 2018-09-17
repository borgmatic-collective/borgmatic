import logging
import re
from datetime import datetime

from .prometheus import prometheus_write_file


def create_metrics(configuration: dict):
    path = configuration['prometheus']['path']
    borg_output_logger = logging.getLogger('borg_output')
    borg_output = borg_output_logger.handlers[0].stream.getvalue()

    metrics = _parse_borg_output(borg_output)

    if 'prometheus' in metrics.keys():
        prometheus_write_file(metrics, path)


def _parse_size(size):
    number, unit = [string.strip() for string in size.split(" ")]
    units = {"B": 1, "kB": 10 ** 3, "MB": 10 ** 6, "GB": 10 ** 9, "TB": 10 ** 12}
    return int(float(number) * units[unit])


def _parse_borg_output(borg_output: str):
    borg_prune = re.findall('=== borg prune ===(.*)=== borg prune end ===', borg_output, re.DOTALL)[0]
    borg_create = re.findall('=== borg create ===(.*)=== borg create end ===', borg_output, re.DOTALL)[0]
    borg_check = re.findall('=== borg check ===(.*)=== borg check end ===', borg_output, re.DOTALL)[0]

    metrics = {
        'last_run': datetime.now().timestamp(),
        'borg_prune': {'deleted_data': {}, 'all_archives': {}, 'chunk_index': {}},
        'borg_create': {'last_archive': {}, 'all_archives': {}, 'chunk_index': {}},
        'borg_check': {},
    }
    original, compressed, deduplicated = re.findall(
        'Deleted data:\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)',
        borg_prune)[0]
    metrics['borg_prune']['deleted_data']['original'] = _parse_size(original)
    metrics['borg_prune']['deleted_data']['compressed'] = _parse_size(compressed)
    metrics['borg_prune']['deleted_data']['deduplicated'] = _parse_size(deduplicated)
    original, compressed, deduplicated = re.findall(
        'All archives:\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)',
        borg_prune)[0]
    metrics['borg_prune']['all_archives']['original'] = _parse_size(original)
    metrics['borg_prune']['all_archives']['compressed'] = _parse_size(compressed)
    metrics['borg_prune']['all_archives']['deduplicated'] = _parse_size(deduplicated)
    unique, total = re.findall('Chunk index:\s+([0-9.]+)\s+([0-9.]+)', self.borg_prune)[0]
    metrics['borg_prune']['chunk_index']['unique'] = unique
    metrics['borg_prune']['chunk_index']['total'] = total
    metrics['borg_prune']['rc'] = 0 if 'terminating with success status, rc 0' in self.borg_prune else 1

    original, compressed, deduplicated = re.findall(
        'This archive:\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)',
        borg_create)[0]
    metrics['borg_create']['last_archive']['original'] = _parse_size(original)
    metrics['borg_create']['last_archive']['compressed'] = _parse_size(compressed)
    metrics['borg_create']['last_archive']['deduplicated'] = _parse_size(deduplicated)
    original, compressed, deduplicated = re.findall(
        'All archives:\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)',
        borg_create)[0]
    metrics['borg_create']['all_archives']['original'] = _parse_size(original)
    metrics['borg_create']['all_archives']['compressed'] = _parse_size(compressed)
    metrics['borg_create']['all_archives']['deduplicated'] = _parse_size(deduplicated)
    unique, total = re.findall('Chunk index:\s+([0-9.]+)\s+([0-9.]+)', borg_create)[0]
    metrics['borg_create']['chunk_index']['unique'] = unique
    metrics['borg_create']['chunk_index']['total'] = total
    metrics['borg_create']['rc'] = 0 if 'terminating with success status, rc 0' in borg_create else 1

    metrics['borg_check'][
        'repository_index'] = 0 if 'Completed repository check, no problems found.' in borg_check else 0
    metrics['borg_check'][
        'archive_consistency'] = 0 if 'Archive consistency check complete, no problems found.' in borg_check else 0
    metrics['borg_check']['rc'] = 0 if 'terminating with success status, rc 0' in borg_check else 1

    return metrics
