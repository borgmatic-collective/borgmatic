---
title: Watchgoose
eleventyNavigation:
  key: Watchgoose
  parent: 🚨 Monitoring
---
<span class="minilink minilink-addedin">New in version 2.1.7</span>
[Watchgoose](https://watchgoose.com/) is a service that "watches your cron jobs,
backups, queues, and scripts" and alerts you "the second one goes late or down."
borgmatic has built-in integration with it. Once you create a Watchgoose account
and project on their site, all you need to do is configure borgmatic with the
unique "Ping URL" for your project. Here's an example:


```yaml
watchgoose:
    ping_url: https://watchgoose.com/addffa72-da17-40ae-be9c-ff591afb942a
```

With this configuration, borgmatic pings your Watchgoose project when a
backup begins, ends, or errors, but only when any of the `create`, `prune`,
`compact`, or `check` actions are run.

You can configure Watchgoose to notify you by a [variety of
mechanisms](https://watchgoose.com/#features) when backups fail
or it doesn't hear from borgmatic for a certain period of time.


### Sending logs

If the actions complete successfully, borgmatic can notify Watchgoose of the
success and includes borgmatic logs in the payload data sent to Watchgoose.
This means that borgmatic logs can show up in the Watchgoose UI, although be
aware that Watchgoose currently has a 10,000 byte limit for the logs in each
ping.

Log sending is disabled by default to avoid revealing private log information to
a third-party service. But to enable the feature, use the `send_logs` option:

```yaml
watchgoose:
    ping_url: https://watchgoose.com/addffa72-da17-40ae-be9c-ff591afb942a
    send_logs: true
```

If an error occurs during any action or hook, borgmatic notifies Watchgoose,
also tacking on logs including the error itself. But the logs are only
included for errors that occur when a `create`, `prune`, `compact`, or `check`
action is run.

You can customize the verbosity of the logs that are sent to Watchgoose with
borgmatic's `--monitoring-verbosity` flag. The `--list` and `--stats` flags may
also be of use. See [create action
documentation](https://torsion.org/borgmatic/reference/command-line/actions/create/)
for more information.

Set the defaults for these flags in your borgmatic configuration via the
`monitoring_verbosity`, `list`, and `statistics` options.


### Full configuration

{% include snippet/configuration/sample.md %}

```yaml
{% include borgmatic/watchgoose.yaml %}
```
