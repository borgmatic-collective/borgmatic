import argparse
import json
import sys


def parse_arguments(*unparsed_arguments):
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('--output', required=True)
    parser.add_argument('--json', action='store_true', required=True)
    parser.add_argument('--list', action='store_true', required=True)

    return parser.parse_args(unparsed_arguments)


BUILTIN_BLOCK_DEVICES = {
    'blockdevices': [
        {'name': 'loop0', 'path': '/dev/loop0', 'mountpoint': None, 'type': 'loop'},
        {'name': 'cryptroot', 'path': '/dev/mapper/cryptroot', 'mountpoint': '/', 'type': 'crypt'},
        {
            'name': 'vgroup-lvolume',
            'path': '/dev/mapper/vgroup-lvolume',
            'mountpoint': '/e2e/mnt/lvolume',
            'type': 'lvm',
        },
        {
            'name': 'vgroup-lvolume-real',
            'path': '/dev/mapper/vgroup-lvolume-real',
            'mountpoint': None,
            'type': 'lvm',
        },
    ]
}


def load_snapshots():
    try:
        return json.load(open('/tmp/fake_lvm.json'))
    except FileNotFoundError:
        return []


def print_logical_volumes_json(arguments, snapshots):
    data = dict(BUILTIN_BLOCK_DEVICES)

    for snapshot in snapshots:
        data['blockdevices'].extend(
            {
                'name': snapshot['lv_name'],
                'path': snapshot['lv_path'],
                'mountpoint': None,
                'type': 'lvm',
            }
            for snapshot in snapshots
        )

    print(json.dumps(data))


def main():
    arguments = parse_arguments(*sys.argv[1:])
    snapshots = load_snapshots()

    assert arguments.output == 'name,path,mountpoint,type'

    print_logical_volumes_json(arguments, snapshots)


if __name__ == '__main__':
    main()
