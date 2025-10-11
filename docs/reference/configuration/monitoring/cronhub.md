---
title: Cronhub
eleventyNavigation:
  key: • Cronhub
  parent: 🚨 Monitoring
---
[Cronhub](https://cronhub.io/) provides "instant alerts when any of your
background jobs fail silently or run longer than expected," and borgmatic has
built-in integration with it. Once you create a Cronhub account and monitor on
their site, all you need to do is configure borgmatic with the unique "Ping
URL" for your monitor. Here's an example:


```yaml
cronhub:
    ping_url: https://cronhub.io/start/1f5e3410-254c-11e8-b61d-55875966d031
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `hooks:` section of your configuration.

With this configuration, borgmatic pings your Cronhub monitor when a backup
begins, ends, or errors, but only when any of the `create`, `prune`,
`compact`, or `check` actions are run. Then, if the actions complete
successfully or errors, borgmatic notifies Cronhub accordingly.

Note that even though you configure borgmatic with the "start" variant of the
ping URL, borgmatic substitutes the correct state into the URL when pinging
Cronhub ("start", "finish", or "fail").

You can configure Cronhub to notify you by a [variety of
mechanisms](https://docs.cronhub.io/integrations.html) when backups fail
or it doesn't hear from borgmatic for a certain period of time.
