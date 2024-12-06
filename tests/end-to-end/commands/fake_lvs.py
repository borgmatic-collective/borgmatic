import argparse
import json
import sys


def parse_arguments(*unparsed_arguments):
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('--report-format', required=True)
    parser.add_argument('--options', required=True)
    parser.add_argument('--select', required=True)

    return parser.parse_args(unparsed_arguments)


def load_snapshots():
    try:
        return json.load(open('/tmp/fake_lvm.json'))
    except FileNotFoundError:
        return []


def print_snapshots_json(arguments, snapshots):
    assert arguments.report_format == 'json'
    assert arguments.options == 'lv_name,lv_path'
    assert arguments.select == 'lv_attr =~ ^s'

    print(
        json.dumps(
            {
                'report': [
                    {
                        'lv': snapshots,
                    }
                ],
                'log': [],
            }
        )
    )


def main():
    arguments = parse_arguments(*sys.argv[1:])
    snapshots = load_snapshots()

    print_snapshots_json(arguments, snapshots)


if __name__ == '__main__':
    main()
