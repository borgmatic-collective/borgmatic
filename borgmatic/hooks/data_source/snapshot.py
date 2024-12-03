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
    directories from it.
    '''
    if not candidate_contained_directories:
        return ()

    contained = tuple(
        candidate
        for candidate in candidate_contained_directories
        if parent_directory == candidate
        or pathlib.PurePosixPath(parent_directory) in pathlib.PurePath(candidate).parents
    )
    candidate_contained_directories -= set(contained)

    return contained
