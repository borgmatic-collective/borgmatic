import argparse
import json
import sys


def parse_arguments(*unparsed_arguments):
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('--snapshot', action='store_true', required=True)
    parser.add_argument('--extents')
    parser.add_argument('--size')
    parser.add_argument('--permission', required=True)
    parser.add_argument('--name', dest='snapshot_name', required=True)
    parser.add_argument('logical_volume_device')

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
    snapshots = load_snapshots()

    assert arguments.extents or arguments.size

    snapshots.append(
        {'lv_name': arguments.snapshot_name, 'lv_path': f'/dev/vgroup/{arguments.snapshot_name}'},
    )

    save_snapshots(snapshots)


if __name__ == '__main__':
    main()
