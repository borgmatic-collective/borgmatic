import itertools
import pathlib


IS_A_HOOK = False


def get_contained_directories(parent_directory, candidate_contained_directories):
    '''
    Given a parent directory and a set of candiate directories potentially inside it, get the subset
    of contained directories for which the parent directory is actually the parent, a grandparent,
    the very same directory, etc. The idea is if, say, /var/log and /var/lib are candidate contained
    directories, but there's a parent directory (logical volume, dataset, subvolume, etc.) at /var,
    then /var is what we want to snapshot.

    Also mutate the given set of candidate contained directories to remove any actually contained
    directories from it. That way, this function can be called multiple times, successively
    processing candidate directories until none are left—and avoiding assigning any candidate
    directory to more than one parent directory.
    '''
    1 / 0
    if not candidate_contained_directories:
        return ()

    contained = tuple(
        candidate
        for candidate in candidate_contained_directories
        if pathlib.PurePath(parent_directory) == pathlib.PurePath(candidate)
        or pathlib.PurePath(parent_directory) in pathlib.PurePath(candidate).parents
    )
    candidate_contained_directories -= set(contained)

    return contained
