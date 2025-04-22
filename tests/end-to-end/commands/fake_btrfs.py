import argparse
import json
import os
import shutil
import sys


def parse_arguments(*unparsed_arguments):
    global_parser = argparse.ArgumentParser(add_help=False)
    action_parsers = global_parser.add_subparsers(dest='action')

    subvolume_parser = action_parsers.add_parser('subvolume')
    subvolume_subparser = subvolume_parser.add_subparsers(dest='subaction')

    list_parser = subvolume_subparser.add_parser('list')
    list_parser.add_argument('-s', dest='snapshots_only', action='store_true')
    list_parser.add_argument('subvolume_path')

    snapshot_parser = subvolume_subparser.add_parser('snapshot')
    snapshot_parser.add_argument('-r', dest='read_only', action='store_true')
    snapshot_parser.add_argument('subvolume_path')
    snapshot_parser.add_argument('snapshot_path')

    delete_parser = subvolume_subparser.add_parser('delete')
    delete_parser.add_argument('snapshot_path')

    property_parser = action_parsers.add_parser('property')
    property_subparser = property_parser.add_subparsers(dest='subaction')
    get_parser = property_subparser.add_parser('get')
    get_parser.add_argument('-t', dest='type')
    get_parser.add_argument('subvolume_path')
    get_parser.add_argument('property_name')

    return (global_parser, global_parser.parse_args(unparsed_arguments))


BUILTIN_SUBVOLUME_LIST_LINES = (
    '261 gen 29 top level 5 path sub',
    '262 gen 29 top level 5 path other',
)
SUBVOLUME_LIST_LINE_PREFIX = '263 gen 29 top level 5 path '


def load_snapshots():
    try:
        return json.load(open('/tmp/fake_btrfs.json'))
    except FileNotFoundError:
        return []


def save_snapshots(snapshot_paths):
    json.dump(snapshot_paths, open('/tmp/fake_btrfs.json', 'w'))


def print_subvolume_list(arguments, snapshot_paths):
    assert arguments.subvolume_path == '/e2e/mnt/subvolume'

    if not arguments.snapshots_only:
        for line in BUILTIN_SUBVOLUME_LIST_LINES:
            print(line)

    for snapshot_path in snapshot_paths:
        print(
            SUBVOLUME_LIST_LINE_PREFIX
            + snapshot_path[snapshot_path.index('.borgmatic-snapshot-') :]
        )


def main():
    (global_parser, arguments) = parse_arguments(*sys.argv[1:])
    snapshot_paths = load_snapshots()

    if not hasattr(arguments, 'subaction'):
        global_parser.print_help()
        sys.exit(1)

    if arguments.subaction == 'list':
        print_subvolume_list(arguments, snapshot_paths)
    elif arguments.subaction == 'snapshot':
        snapshot_paths.append(arguments.snapshot_path)
        save_snapshots(snapshot_paths)

        subdirectory = os.path.join(arguments.snapshot_path, 'subdir')
        os.makedirs(subdirectory, mode=0o700, exist_ok=True)
        test_file = open(os.path.join(subdirectory, 'file.txt'), 'w')
        test_file.write('contents')
        test_file.close()
    elif arguments.subaction == 'delete':
        subdirectory = os.path.join(arguments.snapshot_path, 'subdir')
        shutil.rmtree(subdirectory)

        snapshot_paths = [
            snapshot_path
            for snapshot_path in snapshot_paths
            if snapshot_path.endswith('/' + arguments.snapshot_path)
        ]
        save_snapshots(snapshot_paths)
    elif arguments.action == 'property' and arguments.subaction == 'get':
        print(f'{arguments.property_name}=false')


if __name__ == '__main__':
    main()
