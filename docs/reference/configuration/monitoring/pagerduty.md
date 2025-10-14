---
title: PagerDuty
eleventyNavigation:
  key: PagerDuty
  parent: 🚨 Monitoring
---
In case you're new here: [borgmatic](https://torsion.org/borgmatic/) is
simple, configuration-driven backup software for servers and workstations,
powered by [Borg Backup](https://www.borgbackup.org/).

[PagerDuty](https://www.pagerduty.com/) provides incident monitoring and
alerting. borgmatic has built-in integration that can notify you via PagerDuty
as soon as a backup fails, so you can make sure your backups keep working.

First, create a PagerDuty account and <a
href="https://support.pagerduty.com/docs/services-and-integrations">service</a>
on their site. On the service, add an integration and set the Integration Type
to "borgmatic".

Then, configure borgmatic with the unique "Integration Key" for your service.
Here's an example:


```yaml
pagerduty:
    integration_key: a177cad45bd374409f78906a810a3074
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `hooks:` section of your configuration.

With this configuration, borgmatic creates a PagerDuty event for your service
whenever backups fail, but only when any of the `create`, `prune`, `compact`,
or `check` actions are run. Note that borgmatic does not contact PagerDuty
when a backup starts or when it ends without error.

You can configure PagerDuty to notify you by a [variety of
mechanisms](https://support.pagerduty.com/docs/notifications) when backups
fail.

If you have any issues with the integration, [please contact
us](https://torsion.org/borgmatic/#support-and-contributing).


### Sending logs

<span class="minilink minilink-addedin">New in version 1.9.14</span> borgmatic
logs are included in the payload data sent to PagerDuty. This means that
(truncated) borgmatic logs, including error messages, show up in the PagerDuty
incident UI and corresponding notification emails.

You can customize the verbosity of the logs that are sent with borgmatic's
`--monitoring-verbosity` flag. The `--list` and `--stats` flags may also be of
use. See `borgmatic create --help` for more information.

<span class="minilink minilink-addedin">New in version 2.0.0</span>Set the
defaults for these flags in your borgmatic configuration via the
`monitoring_verbosity`, `list`, and `statistics` options.

If you don't want any logs sent, you can disable log sending by setting
`send_logs` to `false`:

```yaml
pagerduty:
    integration_key: a177cad45bd374409f78906a810a3074
    send_logs: false
```
