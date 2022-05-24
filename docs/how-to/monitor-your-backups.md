---
title: How to monitor your backups
eleventyNavigation:
  key: 🚨 Monitor your backups
  parent: How-to guides
  order: 5
---

## Monitoring and alerting

Having backups is great, but they won't do you a lot of good unless you have
confidence that they're running on a regular basis. That's where monitoring
and alerting comes in.

There are several different ways you can monitor your backups and find out
whether they're succeeding. Which of these you choose to do is up to you and
your particular infrastructure.

### Job runner alerts

The easiest place to start is with failure alerts from the [scheduled job
runner](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#autopilot)
(cron, systemd, etc.) that's running borgmatic. But note that if the job
doesn't even get scheduled (e.g. due to the job runner not running), you
probably won't get an alert at all! Still, this is a decent first line of
defense, especially when combined with some of the other approaches below.

### Commands run on error

The `on_error` hook allows you to run an arbitrary command or script when
borgmatic itself encounters an error running your backups. So for instance,
you can run a script to send yourself a text message alert. But note that if
borgmatic doesn't actually run, this alert won't fire.  See [error
hooks](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#error-hooks)
below for how to configure this.

### Third-party monitoring services

borgmatic integrates with monitoring services like
[Healthchecks](https://healthchecks.io/), [Cronitor](https://cronitor.io),
[Cronhub](https://cronhub.io), and [PagerDuty](https://www.pagerduty.com/) and
pings these services whenever borgmatic runs. That way, you'll receive an
alert when something goes wrong or (for certain hooks) the service doesn't
hear from borgmatic for a configured interval. See [Healthchecks
hook](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#healthchecks-hook),
[Cronitor
hook](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#cronitor-hook),
[Cronhub
hook](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#cronhub-hook),
and [PagerDuty
hook](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#pagerduty-hook)
below for how to configure this.

While these services offer different features, you probably only need to use
one of them at most.

### Third-party monitoring software

You can use traditional monitoring software to consume borgmatic JSON output
and track when the last successful backup occurred. See [scripting
borgmatic](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#scripting-borgmatic)
and [related
software](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#related-software)
below for how to configure this.

### Borg hosting providers

Most [Borg hosting
providers](https://torsion.org/borgmatic/#hosting-providers) include
monitoring and alerting as part of their offering. This gives you a dashboard
to check on all of your backups, and can alert you if the service doesn't hear
from borgmatic for a configured interval.

### Consistency checks

While not strictly part of monitoring, if you really want confidence that your
backups are not only running but are restorable as well, you can configure
particular [consistency
checks](https://torsion.org/borgmatic/docs/how-to/deal-with-very-large-backups/#consistency-check-configuration)
or even script full [extract
tests](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/).


## Error hooks

When an error occurs during a `prune`, `compact`, `create`, or `check` action,
borgmatic can run configurable shell commands to fire off custom error
notifications or take other actions, so you can get alerted as soon as
something goes wrong. Here's a not-so-useful example:

```yaml
hooks:
    on_error:
        - echo "Error while creating a backup or running a backup hook."
```

The `on_error` hook supports interpolating particular runtime variables into
the hook command. Here's an example that assumes you provide a separate shell
script to handle the alerting:

```yaml
hooks:
    on_error:
        - send-text-message.sh "{configuration_filename}" "{repository}"
```

In this example, when the error occurs, borgmatic interpolates runtime values
into the hook command: the borgmatic configuration filename, and the path of
the repository. Here's the full set of supported variables you can use here:

 * `configuration_filename`: borgmatic configuration filename in which the
   error occurred
 * `repository`: path of the repository in which the error occurred (may be
   blank if the error occurs in a hook)
 * `error`: the error message itself
 * `output`: output of the command that failed (may be blank if an error
   occurred without running a command)

Note that borgmatic runs the `on_error` hooks only for `prune`, `compact`,
`create`, or `check` actions or hooks in which an error occurs, and not other
actions. borgmatic does not run `on_error` hooks if an error occurs within a
`before_everything` or `after_everything` hook. For more about hooks, see the
[borgmatic hooks
documentation](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/),
especially the security information.


## Healthchecks hook

[Healthchecks](https://healthchecks.io/) is a service that provides "instant
alerts when your cron jobs fail silently", and borgmatic has built-in
integration with it. Once you create a Healthchecks account and project on
their site, all you need to do is configure borgmatic with the unique "Ping
URL" for your project. Here's an example:


```yaml
hooks:
    healthchecks:
        ping_url: https://hc-ping.com/addffa72-da17-40ae-be9c-ff591afb942a
```

With this hook in place, borgmatic pings your Healthchecks project when a
backup begins, ends, or errors. Specifically, after the <a
href="https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/">`before_backup`
hooks</a> run, borgmatic lets Healthchecks know that it has started if any of
the `prune`, `compact`, `create`, or `check` actions are run.

Then, if the actions complete successfully, borgmatic notifies Healthchecks of
the success after the `after_backup` hooks run, and includes borgmatic logs in
the payload data sent to Healthchecks. This means that borgmatic logs show up
in the Healthchecks UI, although be aware that Healthchecks currently has a
10-kilobyte limit for the logs in each ping.

If an error occurs during any action or hook, borgmatic notifies Healthchecks
after the `on_error` hooks run, also tacking on logs including the error
itself. But the logs are only included for errors that occur when a `prune`,
`compact`, `create`, or `check` action is run.

You can customize the verbosity of the logs that are sent to Healthchecks with
borgmatic's `--monitoring-verbosity` flag. The `--files` and `--stats` flags
may also be of use. See `borgmatic --help` for more information. Additionally,
see the [borgmatic configuration
file](https://torsion.org/borgmatic/docs/reference/configuration/) for
additional Healthchecks options.

You can configure Healthchecks to notify you by a [variety of
mechanisms](https://healthchecks.io/#welcome-integrations) when backups fail
or it doesn't hear from borgmatic for a certain period of time.


## Cronitor hook

[Cronitor](https://cronitor.io/) provides "Cron monitoring and uptime healthchecks
for websites, services and APIs", and borgmatic has built-in
integration with it. Once you create a Cronitor account and cron job monitor on
their site, all you need to do is configure borgmatic with the unique "Ping
API URL" for your monitor. Here's an example:


```yaml
hooks:
    cronitor:
        ping_url: https://cronitor.link/d3x0c1
```

With this hook in place, borgmatic pings your Cronitor monitor when a backup
begins, ends, or errors. Specifically, after the <a
href="https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/">`before_backup`
hooks</a> run, borgmatic lets Cronitor know that it has started if any of the
`prune`, `compact`, `create`, or `check` actions are run. Then, if the actions
complete successfully, borgmatic notifies Cronitor of the success after the
`after_backup` hooks run. And if an error occurs during any action or hook,
borgmatic notifies Cronitor after the `on_error` hooks run.

You can configure Cronitor to notify you by a [variety of
mechanisms](https://cronitor.io/docs/cron-job-notifications) when backups fail
or it doesn't hear from borgmatic for a certain period of time.


## Cronhub hook

[Cronhub](https://cronhub.io/) provides "instant alerts when any of your
background jobs fail silently or run longer than expected", and borgmatic has
built-in integration with it. Once you create a Cronhub account and monitor on
their site, all you need to do is configure borgmatic with the unique "Ping
URL" for your monitor. Here's an example:


```yaml
hooks:
    cronhub:
        ping_url: https://cronhub.io/start/1f5e3410-254c-11e8-b61d-55875966d031
```

With this hook in place, borgmatic pings your Cronhub monitor when a backup
begins, ends, or errors. Specifically, after the <a
href="https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/">`before_backup`
hooks</a> run, borgmatic lets Cronhub know that it has started if any of the
`prune`, `compact`, `create`, or `check` actions are run. Then, if the actions
complete successfully, borgmatic notifies Cronhub of the success after the
`after_backup` hooks run. And if an error occurs during any action or hook,
borgmatic notifies Cronhub after the `on_error` hooks run.

Note that even though you configure borgmatic with the "start" variant of the
ping URL, borgmatic substitutes the correct state into the URL when pinging
Cronhub ("start", "finish", or "fail").

You can configure Cronhub to notify you by a [variety of
mechanisms](https://docs.cronhub.io/integrations.html) when backups fail
or it doesn't hear from borgmatic for a certain period of time.


## PagerDuty hook

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
hooks:
    pagerduty:
        integration_key: a177cad45bd374409f78906a810a3074
```

With this hook in place, borgmatic creates a PagerDuty event for your service
whenever backups fail. Specifically, if an error occurs during a `create`,
`prune`, `compact`, or `check` action, borgmatic sends an event to PagerDuty
before the `on_error` hooks run. Note that borgmatic does not contact
PagerDuty when a backup starts or ends without error.

You can configure PagerDuty to notify you by a [variety of
mechanisms](https://support.pagerduty.com/docs/notifications) when backups
fail.

If you have any issues with the integration, [please contact
us](https://torsion.org/borgmatic/#support-and-contributing).


## Scripting borgmatic

To consume the output of borgmatic in other software, you can include an
optional `--json` flag with `create`, `list`, or `info` to get the output
formatted as JSON.

Note that when you specify the `--json` flag, Borg's other non-JSON output is
suppressed so as not to interfere with the captured JSON. Also note that JSON
output only shows up at the console, and not in syslog.


## Related software

 * [Borgmacator GNOME AppIndicator](https://github.com/N-Coder/borgmacator/)


### Successful backups

`borgmatic list` includes support for a `--successful` flag that only lists
successful (non-checkpoint) backups. This flag works via a basic heuristic: It
assumes that non-checkpoint archive names end with a digit (e.g. from a
timestamp), while checkpoint archive names do not. This means that if you're
using custom archive names that do not end in a digit, the `--successful` flag
will not work as expected.

Combined with a built-in Borg flag like `--last`, you can list the last
successful backup for use in your monitoring scripts. Here's an example
combined with `--json`:

```bash
borgmatic list --successful --last 1 --json
```

Note that this particular combination will only work if you've got a single
backup "series" in your repository. If you're instead backing up, say, from
multiple different hosts into a single repository, then you'll need to get
fancier with your archive listing. See `borg list --help` for more flags.


### Latest backups

All borgmatic actions that accept an "--archive" flag allow you to specify an
archive name of "latest". This lets you get the latest successful archive
without having to first run "borgmatic list" manually, which can be handy in
automated scripts. Here's an example:

```bash
borgmatic info --archive latest
```
