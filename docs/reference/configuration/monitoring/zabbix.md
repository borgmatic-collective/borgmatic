---
title: Zabbix
eleventyNavigation:
  key: • Zabbix
  parent: 🚨 Monitoring
---
<span class="minilink minilink-addedin">New in version 1.9.0</span>
[Zabbix](https://www.zabbix.com/) is an open-source monitoring tool used for
tracking and managing the performance and availability of networks, servers,
and applications in real-time.

This hook does not do any notifications on its own. Instead, it relies on your
Zabbix instance to notify and perform escalations based on the Zabbix
configuration. The `states` defined in the configuration determine which
states will trigger the hook. The value defined in the configuration of each
state is used to populate the data of the configured Zabbix item. If none are
provided, it defaults to a lower-case string of the state.

An example configuration is shown here with all the available options.

```yaml
zabbix:
    server: http://cloud.zabbix.com/zabbix/api_jsonrpc.php
    
    username: myuser
    password: secret
    api_key: b2ecba64d8beb47fc161ae48b164cfd7104a79e8e48e6074ef5b141d8a0aeeca

    host: "borg-server"
    key: borg.status
    itemid: 55105

    start:
        value: "STARTED"
    finish:
        value: "OK"
    fail:
        value: "ERROR"
    states:
        - start
        - finish
        - fail
```

This hook requires the Zabbix server be running version 7.0.

<span class="minilink minilink-addedin">New in version 1.9.3</span> Zabbix 7.2+
is supported as well.


### Authentication methods

Authentication can be accomplished via `api_key` or both `username` and
`password`. If all three are declared, only `api_key` is used.


### Items

borgmatic writes its monitoring updates to a particular Zabbix item, which
you'll need to create in advance. In the Zabbix web UI, [make a new item with a
Type of "Zabbix
trapper"](https://www.zabbix.com/documentation/current/en/manual/config/items/itemtypes/trapper)
and a named Key. The "Type of information" for the item should be "Text", and
"History" designates how much data you want to retain.

When configuring borgmatic with this item to be updated, you can either declare
the `itemid` or both `host` and `key`. If all three are declared, only `itemid`
is used.

Keep in mind that `host` refers to the "Host name" on the Zabbix server and not
the "Visual name".
