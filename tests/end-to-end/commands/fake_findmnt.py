import argparse
import sys


def parse_arguments(*unparsed_arguments):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-t', dest='type')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--list', action='store_true')

    return parser.parse_args(unparsed_arguments)


BUILTIN_FILESYSTEM_MOUNT_OUTPUT = '''{
       "filesystems": [
          {
             "target": "/e2e/mnt/subvolume",
             "source": "/dev/loop0",
             "fstype": "btrfs",
             "options": "rw,relatime,ssd,space_cache=v2,subvolid=5,subvol=/"
          }
       ]
    }
    '''


def print_filesystem_mounts():
    print(BUILTIN_FILESYSTEM_MOUNT_OUTPUT)


def main():
    arguments = parse_arguments(*sys.argv[1:])

    assert arguments.type == 'btrfs'
    assert arguments.json
    assert arguments.list

    print_filesystem_mounts()


if __name__ == '__main__':
    main()
