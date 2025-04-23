from enum import Enum

from packaging.version import parse


class Feature(Enum):
    COMPACT = 1
    ATIME = 2
    NOFLAGS = 3
    NUMERIC_IDS = 4
    UPLOAD_RATELIMIT = 5
    SEPARATE_REPOSITORY_ARCHIVE = 6
    REPO_CREATE = 7
    REPO_LIST = 8
    REPO_INFO = 9
    REPO_DELETE = 10
    MATCH_ARCHIVES = 11
    EXCLUDED_FILES_MINUS = 12
    ARCHIVE_SERIES = 13
    NO_PRUNE_STATS = 14
    DRY_RUN_COMPACT = 15


FEATURE_TO_MINIMUM_BORG_VERSION = {
    Feature.COMPACT: parse('1.2.0a2'),  # borg compact
    Feature.ATIME: parse('1.2.0a7'),  # borg create --atime
    Feature.NOFLAGS: parse('1.2.0a8'),  # borg create --noflags
    Feature.NUMERIC_IDS: parse('1.2.0b3'),  # borg create/extract/mount --numeric-ids
    Feature.UPLOAD_RATELIMIT: parse('1.2.0b3'),  # borg create --upload-ratelimit
    Feature.SEPARATE_REPOSITORY_ARCHIVE: parse('2.0.0a2'),  # --repo with separate archive
    Feature.REPO_CREATE: parse('2.0.0a2'),  # borg repo-create
    Feature.REPO_LIST: parse('2.0.0a2'),  # borg repo-list
    Feature.REPO_INFO: parse('2.0.0a2'),  # borg repo-info
    Feature.REPO_DELETE: parse('2.0.0a2'),  # borg repo-delete
    Feature.MATCH_ARCHIVES: parse('2.0.0b3'),  # borg --match-archives
    Feature.EXCLUDED_FILES_MINUS: parse('2.0.0b5'),  # --list --filter uses "-" for excludes
    Feature.ARCHIVE_SERIES: parse('2.0.0b11'),  # identically named archives form a series
    Feature.NO_PRUNE_STATS: parse('2.0.0b10'),  # prune --stats is not available
    Feature.DRY_RUN_COMPACT: parse('1.4.1'),  # borg compact --dry-run support
}


def available(feature, borg_version):
    '''
    Given a Borg Feature constant and a Borg version string, return whether that feature is
    available in that version of Borg.
    '''
    return FEATURE_TO_MINIMUM_BORG_VERSION[feature] <= parse(borg_version)
