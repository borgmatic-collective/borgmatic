---
title: Loki
eleventyNavigation:
  key: • Loki
  parent: 🚨 Monitoring
---
<span class="minilink minilink-addedin">New in version 1.8.3</span> [Grafana
Loki](https://grafana.com/oss/loki/) is a "horizontally scalable, highly
available, multi-tenant log aggregation system inspired by Prometheus."
borgmatic has built-in integration with Loki, sending both backup status and
borgmatic logs.

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

With this configuration, borgmatic sends its logs to your Loki instance as any
of the `create`, `prune`, `compact`, or `check` actions are run. Then, after
the actions complete, borgmatic notifies Loki of success or failure.

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
you'd like to see your backup logs and statistics in one place.
