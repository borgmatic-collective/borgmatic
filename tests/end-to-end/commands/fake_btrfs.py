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

    show_parser = subvolume_subparser.add_parser('show')
    show_parser.add_argument('subvolume_path')

    snapshot_parser = subvolume_subparser.add_parser('snapshot')
    snapshot_parser.add_argument('-r', dest='read_only', action='store_true')
    snapshot_parser.add_argument('subvolume_path')
    snapshot_parser.add_argument('snapshot_path')

    delete_parser = subvolume_subparser.add_parser('delete')
    delete_parser.add_argument('snapshot_path')

    ensure_deleted_parser = subvolume_subparser.add_parser('ensure_deleted')
    ensure_deleted_parser.add_argument('snapshot_path')

    property_parser = action_parsers.add_parser('property')
    property_subparser = property_parser.add_subparsers(dest='subaction')
    get_parser = property_subparser.add_parser('get')
    get_parser.add_argument('-t', dest='type')
    get_parser.add_argument('subvolume_path')
    get_parser.add_argument('property_name')

    return (global_parser, global_parser.parse_args(unparsed_arguments))


def load_snapshots():
    try:
        return json.load(open('/tmp/fake_btrfs.json'))
    except FileNotFoundError:
        return []


def save_snapshots(snapshot_paths):
    json.dump(snapshot_paths, open('/tmp/fake_btrfs.json', 'w'))


def print_subvolume_show(arguments):
    assert arguments.subvolume_path == '/e2e/mnt/subvolume'

    # borgmatic doesn't currently parse the output of "btrfs subvolume show"—it's just checking the
    # exit code—so what we print in response doesn't matter in this test.
    print('Totally legit btrfs subvolume!')


def main():
    (global_parser, arguments) = parse_arguments(*sys.argv[1:])
    snapshot_paths = load_snapshots()

    if not hasattr(arguments, 'subaction'):
        global_parser.print_help()
        sys.exit(1)

    if arguments.subaction == 'show':
        print_subvolume_show(arguments)
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
    elif arguments.subaction == 'ensure_deleted':
        assert arguments.snapshot_path not in snapshot_paths
    elif arguments.action == 'property' and arguments.subaction == 'get':
        print(f'{arguments.property_name}=false')


if __name__ == '__main__':
    main()
