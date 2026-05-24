import enum


class Path_type(enum.Enum):
    DIRECTORY = 'd'
    LINK = 'l'
    PIPE = 'p'
    FILE = '-'


PATH_TYPE_ICONS = {
    Path_type.DIRECTORY.value: '📁',
    Path_type.LINK.value: '🔗',
    Path_type.PIPE.value: '🚰',
    Path_type.FILE.value: '📄',
}
