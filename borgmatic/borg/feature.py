from enum import Enum

from pkg_resources import parse_version


class Feature(Enum):
    COMPACT = 1
    ATIME = 2
    NOFLAGS = 3
    NUMERIC_IDS = 4
    UPLOAD_RATELIMIT = 5
    SEPARATE_REPOSITORY_ARCHIVE = 6
    RCREATE = 7
    RLIST = 8
    RINFO = 9
    MATCH_ARCHIVES = 10


FEATURE_TO_MINIMUM_BORG_VERSION = {
    Feature.COMPACT: parse_version('1.2.0a2'),  # borg compact
    Feature.ATIME: parse_version('1.2.0a7'),  # borg create --atime
    Feature.NOFLAGS: parse_version('1.2.0a8'),  # borg create --noflags
    Feature.NUMERIC_IDS: parse_version('1.2.0b3'),  # borg create/extract/mount --numeric-ids
    Feature.UPLOAD_RATELIMIT: parse_version('1.2.0b3'),  # borg create --upload-ratelimit
    Feature.SEPARATE_REPOSITORY_ARCHIVE: parse_version('2.0.0a2'),  # --repo with separate archive
    Feature.RCREATE: parse_version('2.0.0a2'),  # borg rcreate
    Feature.RLIST: parse_version('2.0.0a2'),  # borg rlist
    Feature.RINFO: parse_version('2.0.0a2'),  # borg rinfo
    Feature.MATCH_ARCHIVES: parse_version('2.0.0b3'),  # borg --match-archives
}


def available(feature, borg_version):
    '''
    Given a Borg Feature constant and a Borg version string, return whether that feature is
    available in that version of Borg.
    '''
    return FEATURE_TO_MINIMUM_BORG_VERSION[feature] <= parse_version(borg_version)
