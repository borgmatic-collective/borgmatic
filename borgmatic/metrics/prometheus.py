_prometheus_template = """
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


def prometheus_write_file(metrics, path):
    with open(path, 'w') as file:
        file.writelines(_prometheus_template.format(**metrics))
