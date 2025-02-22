import pathlib

IS_A_HOOK = False


def get_contained_patterns(parent_directory, candidate_patterns):
    '''
    Given a parent directory and a set of candidate patterns potentially inside it, get the subset
    of contained patterns for which the parent directory is actually the parent, a grandparent, the
    very same directory, etc. The idea is if, say, /var/log and /var/lib are candidate pattern
    paths, but there's a parent directory (logical volume, dataset, subvolume, etc.) at /var, then
    /var is what we want to snapshot.

    For this function to work, a candidate pattern path can't have any globs or other non-literal
    characters in the initial portion of the path that matches the parent directory. For instance, a
    parent directory of /var would match a candidate pattern path of /var/log/*/data, but not a
    pattern path like /v*/log/*/data.

    The one exception is that if a regular expression pattern path starts with "^", that will get
    stripped off for purposes of matching against a parent directory.

    As part of this, also mutate the given set of candidate patterns to remove any actually
    contained patterns from it. That way, this function can be called multiple times, successively
    processing candidate patterns until none are left—and avoiding assigning any candidate pattern
    to more than one parent directory.
    '''
    if not candidate_patterns:
        return ()

    contained_patterns = tuple(
        candidate
        for candidate in candidate_patterns
        for candidate_path in (pathlib.PurePath(candidate.path.lstrip('^')),)
        if (
            pathlib.PurePath(parent_directory) == candidate_path
            or pathlib.PurePath(parent_directory) in candidate_path.parents
        )
    )
    candidate_patterns -= set(contained_patterns)

    return contained_patterns
