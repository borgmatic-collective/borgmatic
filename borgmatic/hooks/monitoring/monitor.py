import enum

IS_A_HOOK = False


class State(enum.Enum):
    START = 1
    FINISH = 2
    FAIL = 3
    LOG = 4
