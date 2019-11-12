from enum import Enum

MONITOR_HOOK_NAMES = ('healthchecks', 'cronitor', 'cronhub')


class State(Enum):
    START = 1
    FINISH = 2
    FAIL = 3
