---
title: Cronitor
eleventyNavigation:
  key: • Cronitor
  parent: 🚨 Monitoring
---
[Cronitor](https://cronitor.io/) provides "Cron monitoring and uptime healthchecks
for websites, services and APIs," and borgmatic has built-in
integration with it. Once you create a Cronitor account and cron job monitor on
their site, all you need to do is configure borgmatic with the unique "Ping
API URL" for your monitor. Here's an example:


```yaml
cronitor:
    ping_url: https://cronitor.link/d3x0c1
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `hooks:` section of your configuration.

With this configuration, borgmatic pings your Cronitor monitor when a backup
begins, ends, or errors, but only when any of the `create`, `prune`,
`compact`, or `check` actions are run. Then, if the actions complete
successfully or errors, borgmatic notifies Cronitor accordingly.

You can configure Cronitor to notify you by a [variety of
mechanisms](https://cronitor.io/docs/cron-job-notifications) when backups fail
or it doesn't hear from borgmatic for a certain period of time.
