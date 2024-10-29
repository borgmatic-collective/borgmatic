from enum import Enum

MONITOR_HOOK_NAMES = (
    'apprise',
    'cronhub',
    'cronitor',
    'healthchecks',
    'loki',
    'ntfy',
    'pagerduty',
    'uptime_kuma',
    'zabbix',
)


class State(Enum):
    START = 1
    FINISH = 2
    FAIL = 3
    LOG = 4
