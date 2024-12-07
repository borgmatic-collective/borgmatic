import argparse
import os
import sys


def parse_arguments(*unparsed_arguments):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-t', dest='type')
    parser.add_argument('-o', dest='options')
    parser.add_argument('snapshot_name')
    parser.add_argument('mount_point')

    return parser.parse_args(unparsed_arguments)


def main():
    arguments = parse_arguments(*sys.argv[1:])

    assert arguments.options == 'ro'

    subdirectory = os.path.join(arguments.mount_point, 'subdir')
    os.mkdir(subdirectory)
    test_file = open(os.path.join(subdirectory, 'file.txt'), 'w')
    test_file.write('contents')
    test_file.close()


if __name__ == '__main__':
    main()
