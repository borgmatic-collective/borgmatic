---
title: Apprise
eleventyNavigation:
  key: Apprise
  parent: 🚨 Monitoring
---
<span class="minilink minilink-addedin">New in version 1.8.4</span>
[Apprise](https://github.com/caronc/apprise/wiki) is a local notification library
that "allows you to send a notification to almost all of the most popular
[notification services](https://github.com/caronc/apprise/wiki) available to
us today such as: Telegram, Discord, Slack, Amazon SNS, Gotify, etc."

Depending on how you installed borgmatic, it may not have come with Apprise.
For instance, if you originally [installed borgmatic with
pipx](https://torsion.org/borgmatic/how-to/set-up-backups/),
run the following to install Apprise so borgmatic can use it:

```bash
sudo pipx uninstall borgmatic
sudo pipx install borgmatic[Apprise]
```

Omit `sudo` if borgmatic is installed as a non-root user.

Once Apprise is installed, configure borgmatic to notify one or more [Apprise
services](https://github.com/caronc/apprise/wiki). For example:

```yaml
apprise:
    services:
        - url: gotify://hostname/token
          label: gotify
        - url: mastodons://access_key@hostname/@user
          label: mastodon
    states:
        - start
        - finish
        - fail
```

With this configuration, borgmatic pings each of the configured Apprise
services when a backup begins, ends, or errors, but only when any of the
`create`, `prune`, `compact`, or `check` actions are run. (By default, if
`states` is not specified, Apprise services are only pinged on error.)

You can optionally customize the contents of the default messages sent to
these services:

```yaml
apprise:
    services:
        - url: gotify://hostname/token
          label: gotify
    start:
        title: Ping!
        body: Starting backup process.
    finish:
        title: Ping!
        body: Backups successfully made.
    fail:
        title: Ping!
        body: Your backups have failed.
    states:
        - start
        - finish
        - fail
```


### Sending logs

<span class="minilink minilink-addedin">New in version 1.8.9</span> borgmatic
can include logs in the body data sent to your Apprise services when a backup
finishes or fails. There is a `send_logs` option to enable or disable log
sending:

```yaml
apprise:
    services:
        - url: gotify://hostname/token
          label: gotify
    send_logs: true
```

<span class="minilink minilink-addedin">New in version 2.1.0</span> To avoid
revealing private log information to third-party services, logs are no longer
sent by default when `send_logs` is omitted.

<span class="minilink minilink-addedin">Prior to version 2.1.0</span> Logs were
sent by default when `send_logs` was omitted.

You can customize the verbosity of the logs that are sent with borgmatic's
`--monitoring-verbosity` flag. The `--list` and `--stats` flags may also be of
use. See [create action
documentation](https://torsion.org/borgmatic/reference/command-line/actions/create/)
for more information.

<span class="minilink minilink-addedin">New in version 2.0.0</span>Set the
defaults for these flags in your borgmatic configuration via the
`monitoring_verbosity`, `list`, and `statistics` options.

To limit the size of logs sent to Apprise services, set `logs_size_limit` to a
number of bytes:

```yaml
apprise:
    services:
        - url: gotify://hostname/token
          label: gotify
    send_logs: true
    logs_size_limit: 500
```

This may be necessary for some services that reject large requests.


### Full configuration

{% include snippet/configuration/sample.md %}

```yaml
{% include borgmatic/apprise.yaml %}
```
