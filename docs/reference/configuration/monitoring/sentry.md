---
title: Sentry
eleventyNavigation:
  key: Sentry
  parent: 🚨 Monitoring
---
<span class="minilink minilink-addedin">New in version 1.9.7</span>
[Sentry](https://sentry.io/) is an application monitoring service that
includes cron-style monitoring (either cloud-hosted or
[self-hosted](https://develop.sentry.dev/self-hosted/)).

To get started, create a [Sentry cron
monitor](https://docs.sentry.io/product/crons/) in the Sentry UI. Under
"Instrument your monitor," select "Sentry CLI" and copy the URL value for the
displayed
[`SENTRY_DSN`](https://docs.sentry.io/concepts/key-terms/dsn-explainer/)
environment variable into borgmatic's Sentry `data_source_name_url`
configuration option. For example:

```yaml
sentry:
    data_source_name_url: https://5f80ec@o294220.ingest.us.sentry.io/203069
    monitor_slug: mymonitor
```

The `monitor_slug` value comes from the "Monitor Slug" under "Cron Details" on
the same Sentry monitor page.

The `environment` value optionally specifies the enviroment that is used in
Sentry.

With this configuration, borgmatic pings Sentry whenever borgmatic starts,
finishes, or fails, but only when any of the `create`, `prune`, `compact`, or
`check` actions are run. You can optionally override the start/finish/fail
behavior with the `states` configuration option. For instance, to only ping
Sentry on failure:

```yaml
sentry:
    data_source_name_url: https://5f80ec@o294220.ingest.us.sentry.io/203069
    monitor_slug: mymonitor
    environment: myenvironment
    states:
      - fail
```
