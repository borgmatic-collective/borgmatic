import argparse
import sys


def parse_arguments(*unparsed_arguments):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-n', dest='headings', action='store_false', default=True)
    parser.add_argument('-t', dest='type')

    return parser.parse_args(unparsed_arguments)


BUILTIN_FILESYSTEM_MOUNT_LINES = (
    '/mnt/subvolume /dev/loop1 btrfs rw,relatime,ssd,space_cache=v2,subvolid=5,subvol=/',
)


def print_filesystem_mounts(arguments):
    for line in BUILTIN_FILESYSTEM_MOUNT_LINES:
        print(line)


def main():
    arguments = parse_arguments(*sys.argv[1:])

    assert not arguments.headings
    assert arguments.type == 'btrfs'

    print_filesystem_mounts(arguments)


if __name__ == '__main__':
    main()
