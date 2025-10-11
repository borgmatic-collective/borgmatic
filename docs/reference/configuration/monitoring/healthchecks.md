---
title: Healthchecks
eleventyNavigation:
  key: • Healthchecks
  parent: 🚨 Monitoring
---
[Healthchecks](https://healthchecks.io/) is a service that provides "instant
alerts when your cron jobs fail silently," and borgmatic has built-in
integration with it. Once you create a Healthchecks account and project on
their site, all you need to do is configure borgmatic with the unique "Ping
URL" for your project. Here's an example:


```yaml
healthchecks:
    ping_url: https://hc-ping.com/addffa72-da17-40ae-be9c-ff591afb942a
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `hooks:` section of your configuration.

With this configuration, borgmatic pings your Healthchecks project when a
backup begins, ends, or errors, but only when any of the `create`, `prune`,
`compact`, or `check` actions are run.

Then, if the actions complete successfully, borgmatic notifies Healthchecks of
the success and includes borgmatic logs in the payload data sent to
Healthchecks. This means that borgmatic logs show up in the Healthchecks UI,
although be aware that Healthchecks currently has a 100-kilobyte limit for the
logs in each ping.

If an error occurs during any action or hook, borgmatic notifies Healthchecks,
also tacking on logs including the error itself. But the logs are only
included for errors that occur when a `create`, `prune`, `compact`, or `check`
action is run.

You can customize the verbosity of the logs that are sent to Healthchecks with
borgmatic's `--monitoring-verbosity` flag. The `--list` and `--stats` flags
may also be of use. See `borgmatic create --help` for more information.
Additionally, see the [borgmatic configuration
file](https://torsion.org/borgmatic/reference/configuration/) for
additional Healthchecks options.

<span class="minilink minilink-addedin">New in version 2.0.0</span>Set the
defaults for these flags in your borgmatic configuration via the
`monitoring_verbosity`, `list`, and `statistics` options.

You can configure Healthchecks to notify you by a [variety of
mechanisms](https://healthchecks.io/#welcome-integrations) when backups fail
or it doesn't hear from borgmatic for a certain period of time.
