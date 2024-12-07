import argparse
import json
import sys


def parse_arguments(*unparsed_arguments):
    global_parser = argparse.ArgumentParser(add_help=False)
    action_parsers = global_parser.add_subparsers(dest='action')

    list_parser = action_parsers.add_parser('list')
    list_parser.add_argument('-H', dest='header', action='store_false', default=True)
    list_parser.add_argument('-t', dest='type', default='filesystem')
    list_parser.add_argument('-o', dest='properties', default='name,used,avail,refer,mountpoint')

    snapshot_parser = action_parsers.add_parser('snapshot')
    snapshot_parser.add_argument('name')

    destroy_parser = action_parsers.add_parser('destroy')
    destroy_parser.add_argument('name')

    return global_parser.parse_args(unparsed_arguments)


BUILTIN_DATASETS = (
    {
        'name': 'pool',
        'used': '256K',
        'avail': '23.7M',
        'refer': '25K',
        'mountpoint': '/pool',
    },
    {
        'name': 'pool/dataset',
        'used': '256K',
        'avail': '23.7M',
        'refer': '25K',
        'mountpoint': '/pool/dataset',
    },
)


def load_snapshots():
    try:
        return json.load(open('/tmp/fake_zfs.json'))
    except FileNotFoundError:
        return []


def save_snapshots(snapshots):
    json.dump(snapshots, open('/tmp/fake_zfs.json', 'w'))


def print_dataset_list(arguments, datasets, snapshots):
    properties = arguments.properties.split(',')
    data = (
        (tuple(property_name.upper() for property_name in properties),) if arguments.header else ()
    ) + tuple(
        tuple(dataset.get(property_name, '-') for property_name in properties)
        for dataset in (snapshots if arguments.type == 'snapshot' else datasets)
    )

    if not data:
        return

    for data_row in data:
        print('\t'.join(data_row))


def main():
    arguments = parse_arguments(*sys.argv[1:])
    snapshots = load_snapshots()

    if arguments.action == 'list':
        print_dataset_list(arguments, BUILTIN_DATASETS, snapshots)
    elif arguments.action == 'snapshot':
        snapshots.append(
            {
                'name': arguments.name,
                'used': '0B',
                'avail': '-',
                'refer': '25K',
                'mountpoint': '-',
            },
        )
        save_snapshots(snapshots)
    elif arguments.action == 'destroy':
        snapshots = [snapshot for snapshot in snapshots if snapshot['name'] != arguments.name]
        save_snapshots(snapshots)


if __name__ == '__main__':
    main()
