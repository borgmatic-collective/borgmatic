import argparse
import os
import shutil
import sys


def parse_arguments(*unparsed_arguments):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('mount_point')

    return parser.parse_args(unparsed_arguments)


def main():
    arguments = parse_arguments(*sys.argv[1:])

    subdirectory = os.path.join(arguments.mount_point, 'subdir')
    shutil.rmtree(subdirectory)


if __name__ == '__main__':
    main()
