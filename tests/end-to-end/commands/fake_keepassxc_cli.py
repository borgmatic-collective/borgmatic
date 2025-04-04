import argparse
import sys


def parse_arguments(*unparsed_arguments):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('command')
    parser.add_argument('--show-protected', action='store_true')
    parser.add_argument('--attributes')
    parser.add_argument('database_path')
    parser.add_argument('attribute_name')

    return parser.parse_args(unparsed_arguments)


def main():
    arguments = parse_arguments(*sys.argv[1:])

    assert arguments.command == 'show'
    assert arguments.show_protected
    assert arguments.attributes == 'Password'
    assert arguments.database_path.endswith('.kdbx')
    assert arguments.attribute_name

    print('test')


if __name__ == '__main__':
    main()
