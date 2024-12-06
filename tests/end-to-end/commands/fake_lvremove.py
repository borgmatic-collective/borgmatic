import argparse
import json
import sys


def parse_arguments(*unparsed_arguments):
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('--force', action='store_true', required=True)
    parser.add_argument('snapshot_device')

    return parser.parse_args(unparsed_arguments)


def load_snapshots():
    try:
        return json.load(open('/tmp/fake_lvm.json'))
    except FileNotFoundError:
        return []


def save_snapshots(snapshots):
    json.dump(snapshots, open('/tmp/fake_lvm.json', 'w'))


def main():
    arguments = parse_arguments(*sys.argv[1:])

    snapshots = [
        snapshot for snapshot in load_snapshots()
        if snapshot['lv_path'] == arguments.snapshot_device
    ]

    save_snapshots(snapshots)


if __name__ == '__main__':
    main()
