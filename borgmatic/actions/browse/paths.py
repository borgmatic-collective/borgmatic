import enum


class Path_type(enum.Enum):
    DIRECTORY = 'd'
    LINK = 'l'
    FILE = '-'


PATH_TYPE_ICONS = {
    Path_type.DIRECTORY.value: '📁',
    Path_type.LINK.value: '🔗',
    Path_type.FILE.value: '📄',
}
