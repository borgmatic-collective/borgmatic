import itertools


def make_flags(name, value):
    '''
    Given a flag name and its value, return it formatted as Borg-compatible flags.
    '''
    if not value:
        return ()

    flag = '--{}'.format(name.replace('_', '-'))

    if value is True:
        return (flag,)

    return (flag, str(value))


def make_flags_from_arguments(arguments, excludes=()):
    '''
    Given borgmatic command-line arguments as an instance of argparse.Namespace, and optionally a
    list of named arguments to exclude, generate and return the corresponding Borg command-line
    flags as a tuple.
    '''
    return tuple(
        itertools.chain.from_iterable(
            make_flags(name, value=getattr(arguments, name))
            for name in sorted(vars(arguments))
            if name not in excludes and not name.startswith('_')
        )
    )
