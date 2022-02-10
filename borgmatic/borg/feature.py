from enum import Enum

from pkg_resources import parse_version


class Feature(Enum):
    COMPACT = 1
    ATIME = 2


FEATURE_TO_MINIMUM_BORG_VERSION = {
    Feature.COMPACT: parse_version('1.2.0a2'),
    Feature.ATIME: parse_version('1.2.0a7'),
}


def available(feature, borg_version):
    '''
    Given a Borg Feature constant and a Borg version string, return whether that feature is
    available in that version of Borg.
    '''
    return FEATURE_TO_MINIMUM_BORG_VERSION[feature] <= parse_version(borg_version)
