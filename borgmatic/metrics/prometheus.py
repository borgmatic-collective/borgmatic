import re
from datetime import datetime

tmplt = """
borg_last_run {last_run}
borg_prune_deleted_data_bytes{{size="original"}} {borg_prune[deleted_data][original]}
borg_prune_deleted_data_bytes{{size="compressed"}} {borg_prune[deleted_data][compressed]}
borg_prune_deleted_data_bytes{{size="deduplicated"}} {borg_prune[deleted_data][deduplicated]}
borg_prune_all_archives_bytes{{size="original"}} {borg_prune[all_archives][original]}
borg_prune_all_archives_bytes{{size="compressed"}} {borg_prune[all_archives][compressed]}
borg_prune_all_archives_bytes{{size="deduplicated"}} {borg_prune[all_archives][deduplicated]}
borg_prune_chunk_index_count{{type="unique"}} {borg_prune[chunk_index][unique]}
borg_prune_chunk_index_count{{type="total"}} {borg_prune[chunk_index][total]}
borg_prune_rc {borg_prune[rc]}

borg_create_last_archive_bytes{{size="original"}} {borg_create[last_archive][original]}
borg_create_last_archive_bytes{{size="compressed"}} {borg_create[last_archive][compressed]}
borg_create_last_archive_bytes{{size="deduplicated"}} {borg_create[last_archive][deduplicated]}
borg_create_all_archives_bytes{{size="original"}} {borg_create[all_archives][original]}
borg_create_all_archives_bytes{{size="compressed"}} {borg_create[all_archives][compressed]}
borg_create_all_archives_bytes{{size="deduplicated"}} {borg_create[all_archives][deduplicated]}
borg_create_chunk_index_count{{type="unique"}} {borg_create[chunk_index][unique]}
borg_create_chunk_index_count{{type="total"}} {borg_create[chunk_index][total]}
borg_create_rc {borg_create[rc]}

borg_check_repository_index_problems {borg_check[repository_index]}
borg_check_archive_consistency_problems {borg_check[archive_consistency]}
borg_check_rc {borg_check[rc]}
"""

units = {"B": 1, "kB": 10 ** 3, "MB": 10 ** 6, "GB": 10 ** 9, "TB": 10 ** 12}


def parse_size(size):
    number, unit = [string.strip() for string in size.split(" ")]
    return int(float(number) * units[unit])


class PrometheusOutput:
    def __init__(self, borg_output: str):
        self.borg_output = borg_output
        self.borg_prune = re.findall('=== borg prune ===(.*)=== borg prune end ===', borg_output, re.DOTALL)[0]
        self.borg_create = re.findall('=== borg create ===(.*)=== borg create end ===', borg_output, re.DOTALL)[0]
        self.borg_check = re.findall('=== borg check ===(.*)=== borg check end ===', borg_output, re.DOTALL)[0]

        numbers = {
            'last_run': datetime.now().timestamp(),
            'borg_prune': {'deleted_data': {}, 'all_archives': {}, 'chunk_index': {}},
            'borg_create': {'last_archive': {}, 'all_archives': {}, 'chunk_index': {}},
            'borg_check': {},
        }
        orig, comp, dedup = re.findall(
            'Deleted data:\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)',
            self.borg_prune)[0]
        numbers['borg_prune']['deleted_data']['original'] = parse_size(orig)
        numbers['borg_prune']['deleted_data']['compressed'] = parse_size(comp)
        numbers['borg_prune']['deleted_data']['deduplicated'] = parse_size(dedup)
        orig, comp, dedup = re.findall(
            'All archives:\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)',
            self.borg_prune)[0]
        numbers['borg_prune']['all_archives']['original'] = parse_size(orig)
        numbers['borg_prune']['all_archives']['compressed'] = parse_size(comp)
        numbers['borg_prune']['all_archives']['deduplicated'] = parse_size(dedup)
        unique, total = re.findall('Chunk index:\s+([0-9.]+)\s+([0-9.]+)', self.borg_prune)[0]
        numbers['borg_prune']['chunk_index']['unique'] = unique
        numbers['borg_prune']['chunk_index']['total'] = total
        numbers['borg_prune']['rc'] = 0 if 'terminating with success status, rc 0' in self.borg_prune else 1

        orig, comp, dedup = re.findall(
            'This archive:\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)',
            self.borg_create)[0]
        numbers['borg_create']['last_archive']['original'] = parse_size(orig)
        numbers['borg_create']['last_archive']['compressed'] = parse_size(comp)
        numbers['borg_create']['last_archive']['deduplicated'] = parse_size(dedup)
        orig, comp, dedup = re.findall(
            'All archives:\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)\s+(-?[0-9.]+ [a-zA-Z]?B)',
            self.borg_create)[0]
        numbers['borg_create']['all_archives']['original'] = parse_size(orig)
        numbers['borg_create']['all_archives']['compressed'] = parse_size(comp)
        numbers['borg_create']['all_archives']['deduplicated'] = parse_size(dedup)
        unique, total = re.findall('Chunk index:\s+([0-9.]+)\s+([0-9.]+)', self.borg_create)[0]
        numbers['borg_create']['chunk_index']['unique'] = unique
        numbers['borg_create']['chunk_index']['total'] = total
        numbers['borg_create']['rc'] = 0 if 'terminating with success status, rc 0' in self.borg_create else 1

        numbers['borg_check']['repository_index'] = 0 if 'Completed repository check, no problems found.' in self.borg_check else 0
        numbers['borg_check']['archive_consistency'] = 0 if 'Archive consistency check complete, no problems found.' in self.borg_check else 0
        numbers['borg_check']['rc'] = 0 if 'terminating with success status, rc 0' in self.borg_check else 1

        self.numbers = numbers

    def write_file(self, path: str):
        with open(path, 'w') as file:
            file.writelines(tmplt.format(**self.numbers))
