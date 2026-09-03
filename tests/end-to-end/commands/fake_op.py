import sys


def main():
    args = sys.argv[1:]

    assert args[0] == 'read'
    assert args[1] == '--no-newline'
    assert args[2].startswith('op://')

    print('test')


if __name__ == '__main__':
    main()
