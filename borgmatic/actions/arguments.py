import argparse


def update_arguments(arguments, **updates):
    '''
    Given an argparse.Namespace instance of command-line arguments and one or more keyword argument
    updates to perform, return a copy of the arguments with those updates applied.
    '''
    return argparse.Namespace(**dict(vars(arguments), **updates))
