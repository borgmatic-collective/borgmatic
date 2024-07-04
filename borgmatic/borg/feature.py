from enum import Enum

from packaging.version import parse


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
    RDELETE = 10
    MATCH_ARCHIVES = 11
    EXCLUDED_FILES_MINUS = 12


FEATURE_TO_MINIMUM_BORG_VERSION = {
    Feature.COMPACT: parse('1.2.0a2'),  # borg compact
    Feature.ATIME: parse('1.2.0a7'),  # borg create --atime
    Feature.NOFLAGS: parse('1.2.0a8'),  # borg create --noflags
    Feature.NUMERIC_IDS: parse('1.2.0b3'),  # borg create/extract/mount --numeric-ids
    Feature.UPLOAD_RATELIMIT: parse('1.2.0b3'),  # borg create --upload-ratelimit
    Feature.SEPARATE_REPOSITORY_ARCHIVE: parse('2.0.0a2'),  # --repo with separate archive
    Feature.RCREATE: parse('2.0.0a2'),  # borg rcreate
    Feature.RLIST: parse('2.0.0a2'),  # borg rlist
    Feature.RINFO: parse('2.0.0a2'),  # borg rinfo
    Feature.RDELETE: parse('2.0.0a2'),  # borg rdelete
    Feature.MATCH_ARCHIVES: parse('2.0.0b3'),  # borg --match-archives
    Feature.EXCLUDED_FILES_MINUS: parse('2.0.0b5'),  # --list --filter uses "-" for excludes
}


def available(feature, borg_version):
    '''
    Given a Borg Feature constant and a Borg version string, return whether that feature is
    available in that version of Borg.
    '''
    return FEATURE_TO_MINIMUM_BORG_VERSION[feature] <= parse(borg_version)
