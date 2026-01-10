---
title: Loki
eleventyNavigation:
  key: Loki
  parent: 🚨 Monitoring
---
<span class="minilink minilink-addedin">New in version 1.8.3</span> [Grafana
Loki](https://grafana.com/oss/loki/) is a "horizontally scalable, highly
available, multi-tenant log aggregation system inspired by Prometheus."
borgmatic has built-in integration with Loki, sending both backup status and
optionally borgmatic logs.

You can configure borgmatic to use either a [self-hosted Loki
instance](https://grafana.com/docs/loki/latest/installation/) or [a Grafana
Cloud account](https://grafana.com/auth/sign-up/create-user). Start by setting
your Loki API push URL. Here's an example:

```yaml
loki:
    url: http://localhost:3100/loki/api/v1/push

    labels:
        app: borgmatic
        hostname: example.org
```

With this configuration, borgmatic notifies your Loki instance of starting,
success, or failure when any of the `create`, `prune`, `compact`, or `check`
actions run.

This hook supports sending arbitrary labels to Loki. At least one label is
required.

There are also a few placeholders you can optionally use as label values:

 * `__config`: name of the borgmatic configuration file
 * `__config_path`: full path of the borgmatic configuration file
 * `__hostname`: the local machine hostname

These placeholders are only substituted for the whole label value, not
interpolated into a larger string. For instance:

```yaml
loki:
    url: http://localhost:3100/loki/api/v1/push

    labels:
        app: borgmatic
        config: __config
        hostname: __hostname
```

Also check out this [Loki dashboard for
borgmatic](https://grafana.com/grafana/dashboards/20736-borgmatic-logs/) if
you'd like to see your backup logs and statistics in one place. Note that it
does require sending logs (see below).


### Sending logs

borgmatic can include logs in the data sent to Loki when a backup starts,
finishes, or fails.

<span class="minilink minilink-addedin">New in version 2.1.0</span> There is a
`send_logs` option to enable log sending:

```yaml
loki:
    url: http://localhost:3100/loki/api/v1/push

    labels:
        app: borgmatic

    send_logs: true
```

To avoid revealing private log information to third-party services, log sending
is not enabled by default when `send_logs` is omitted.

<span class="minilink minilink-addedin">Prior to version 2.1.0</span> Logs were
sent by default, and the `send_logs` option was not yet supported.

You can customize the verbosity of the logs that are sent with borgmatic's
`--monitoring-verbosity` flag. The `--list` and `--stats` flags may also be of
use. See [create action
documentation](https://torsion.org/borgmatic/reference/command-line/actions/create/)
for more information.

<span class="minilink minilink-addedin">New in version 2.0.0</span>Set the
defaults for these flags in your borgmatic configuration via the
`monitoring_verbosity`, `list`, and `statistics` options.
