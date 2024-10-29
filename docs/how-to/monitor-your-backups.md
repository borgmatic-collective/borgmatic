---
title: How to monitor your backups
eleventyNavigation:
  key: 🚨 Monitor your backups
  parent: How-to guides
  order: 6
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

borgmatic integrates with these monitoring services and libraries, pinging
them as backups happen:

 * [Apprise](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#apprise-hook)
 * [Cronhub](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#cronhub-hook)
 * [Cronitor](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#cronitor-hook)
 * [Grafana Loki](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#loki-hook)
 * [Healthchecks](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#healthchecks-hook)
 * [ntfy](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#ntfy-hook)
 * [PagerDuty](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#pagerduty-hook)
 * [Uptime Kuma](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#uptime-kuma-hook)
 * [Zabbix](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#zabbix-hook)

The idea is that you'll receive an alert when something goes wrong or when the
service doesn't hear from borgmatic for a configured interval (if supported).
See the documentation links above for configuration information.

While these services and libraries offer different features, you probably only
need to use one of them at most.


### Third-party monitoring software

You can use traditional monitoring software to consume borgmatic JSON output
and track when the last successful backup occurred. See [scripting
borgmatic](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#scripting-borgmatic)
below for how to configure this.

### Borg hosting providers

Most [Borg hosting
providers](https://torsion.org/borgmatic/#hosting-providers) include
monitoring and alerting as part of their offering. This gives you a dashboard
to check on all of your backups, and can alert you if the service doesn't hear
from borgmatic for a configured interval.

### Consistency checks

While not strictly part of monitoring, if you want confidence that your
backups are not only running but are restorable as well, you can configure
particular [consistency
checks](https://torsion.org/borgmatic/docs/how-to/deal-with-very-large-backups/#consistency-check-configuration)
or even script full [extract
tests](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/).


## Error hooks

When an error occurs during a `create`, `prune`, `compact`, or `check` action,
borgmatic can run configurable shell commands to fire off custom error
notifications or take other actions, so you can get alerted as soon as
something goes wrong. Here's a not-so-useful example:

```yaml
on_error:
    - echo "Error while creating a backup or running a backup hook."
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `hooks:` section of your configuration.

The `on_error` hook supports interpolating particular runtime variables into
the hook command. Here's an example that assumes you provide a separate shell
script to handle the alerting:

```yaml
on_error:
    - send-text-message.sh {configuration_filename} {repository}
```

In this example, when the error occurs, borgmatic interpolates runtime values
into the hook command: the borgmatic configuration filename and the path of
the repository. Here's the full set of supported variables you can use here:

 * `configuration_filename`: borgmatic configuration filename in which the
   error occurred
 * `repository`: path of the repository in which the error occurred (may be
   blank if the error occurs in a hook)
 * `error`: the error message itself
 * `output`: output of the command that failed (may be blank if an error
   occurred without running a command)

Note that borgmatic runs the `on_error` hooks only for `create`, `prune`,
`compact`, or `check` actions/hooks in which an error occurs and not other
actions. borgmatic does not run `on_error` hooks if an error occurs within a
`before_everything` or `after_everything` hook. For more about hooks, see the
[borgmatic hooks
documentation](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/),
especially the security information.

<span class="minilink minilink-addedin">New in version 1.8.7</span> borgmatic
automatically escapes these interpolated values to prevent shell injection
attacks. One implication of this change is that you shouldn't wrap the
interpolated values in your own quotes, as that will interfere with the
quoting performed by borgmatic and result in your command receiving incorrect
arguments. For instance, this won't work:


```yaml
on_error:
    # Don't do this! It won't work, as the {error} value is already quoted.
    - send-text-message.sh "Uh oh: {error}"
```

Do this instead:

```yaml
on_error:
    - send-text-message.sh {error}
```


## Healthchecks hook

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
file](https://torsion.org/borgmatic/docs/reference/configuration/) for
additional Healthchecks options.

You can configure Healthchecks to notify you by a [variety of
mechanisms](https://healthchecks.io/#welcome-integrations) when backups fail
or it doesn't hear from borgmatic for a certain period of time.


## Cronitor hook

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


## Cronhub hook

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


## ntfy hook

<span class="minilink minilink-addedin">New in version 1.6.3</span>
[ntfy](https://ntfy.sh) is a free, simple, service (either hosted or
self-hosted) which offers simple pub/sub push notifications to multiple
platforms including [web](https://ntfy.sh/stats),
[Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) and
[iOS](https://apps.apple.com/us/app/ntfy/id1625396347).

Since push notifications for regular events might soon become quite annoying,
this hook only fires on any errors by default in order to instantly alert you
to issues. The `states` list can override this. Each state can have its own
custom messages, priorities and tags or, if none are provided, will use the
default.

An example configuration is shown here with all the available options,
including [priorities](https://ntfy.sh/docs/publish/#message-priority) and
[tags](https://ntfy.sh/docs/publish/#tags-emojis):

```yaml
ntfy:
    topic: my-unique-topic
    server: https://ntfy.my-domain.com
    username: myuser
    password: secret

    start:
        title: A borgmatic backup started
        message: Watch this space...
        tags: borgmatic
        priority: min
    finish:
        title: A borgmatic backup completed successfully
        message: Nice!
        tags: borgmatic,+1
        priority: min
    fail:
        title: A borgmatic backup failed
        message: You should probably fix it
        tags: borgmatic,-1,skull
        priority: max
    states:
        - start
        - finish
        - fail
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
the `ntfy:` option in the `hooks:` section of your configuration.

<span class="minilink minilink-addedin">New in version 1.8.9</span> Instead of
`username`/`password`, you can specify an [ntfy access
token](https://docs.ntfy.sh/config/#access-tokens):

```yaml
ntfy:
    topic: my-unique-topic
    server: https://ntfy.my-domain.com
    access_token: tk_AgQdq7mVBoFD37zQVN29RhuMzNIz2
````

## Loki hook

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
```

With this configuration, borgmatic sends its logs to your Loki instance as any
of the `create`, `prune`, `compact`, or `check` actions are run. Then, after
the actions complete, borgmatic notifies Loki of success or failure.

This hook supports sending arbitrary labels to Loki. For instance:

```yaml
loki:
    url: http://localhost:3100/loki/api/v1/push

    labels:
        app: borgmatic
        hostname: example.org
```

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


## Apprise hook

<span class="minilink minilink-addedin">New in version 1.8.4</span>
[Apprise](https://github.com/caronc/apprise/wiki) is a local notification library
that "allows you to send a notification to almost all of the most popular
[notification services](https://github.com/caronc/apprise/wiki) available to
us today such as: Telegram, Discord, Slack, Amazon SNS, Gotify, etc."

Depending on how you installed borgmatic, it may not have come with Apprise.
For instance, if you originally [installed borgmatic with
pipx](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#installation),
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

<span class="minilink minilink-addedin">New in version 1.8.9</span> borgmatic
logs are automatically included in the body data sent to your Apprise services
when a backup finishes or fails.

You can customize the verbosity of the logs that are sent with borgmatic's
`--monitoring-verbosity` flag. The `--list` and `--stats` flags may also be of
use. See `borgmatic create --help` for more information.

If you don't want any logs sent, you can disable this feature by setting
`send_logs` to `false`:

```yaml
apprise:
    services:
        - url: gotify://hostname/token
          label: gotify
    send_logs: false
```

Or to limit the size of logs sent to Apprise services:

```yaml
apprise:
    services:
        - url: gotify://hostname/token
          label: gotify
    logs_size_limit: 500
```

This may be necessary for some services that reject large requests.

See the [configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/) for
details.

## Uptime Kuma hook

<span class="minilink minilink-addedin">New in version 1.8.13</span> [Uptime
Kuma](https://uptime.kuma.pet) is a self-hosted monitoring tool and can
provide a Push monitor type to accept HTTP `GET` requests from a service
instead of contacting it directly.

Uptime Kuma allows you to see a history of monitor states and can in turn
alert via ntfy, Gotify, Matrix, Apprise, Email, and many more.

An example configuration is shown here with all the available options:

```yaml
uptime_kuma:
    push_url: https://kuma.my-domain.com/api/push/abcd1234
    states:
        - start
        - finish
        - fail
```

The `push_url` is provided to your from your Uptime Kuma service and
originally includes a query string—the text including and after the question
mark (`?`). But please do not include the query string in the `push_url`
configuration; borgmatic will add this automatically depending on the state of
your backup. 

Using `start`, `finish` and `fail` states means you will get two "up beats" in
Uptime Kuma for successful backups and the ability to see failures if and when
the backup started (was there a `start` beat?).

A reasonable base-level configuration for an Uptime Kuma Monitor for a backup
is below:

```ini
# These are to be entered into Uptime Kuma and not into your borgmatic
# configuration.

# Push monitors wait for the client to contact Uptime Kuma instead of Uptime
# Kuma contacting the client. This is perfect for backup monitoring.
Monitor Type = Push

Heartbeat Interval = 90000     # = 25 hours = 1 day + 1 hour

# Wait 6 times the Heartbeat Retry (below) before logging a heartbeat missed.
Retries = 6

# Multiplied by Retries this gives a grace period within which the monitor
# goes into the "Pending" state.
Heartbeat Retry = 360          # = 10 minutes

# For each Heartbeat Interval if the backup fails repeatedly, a notification
# is sent each time.
Resend Notification every X times = 1
```

## Zabbix hook

<span class="minilink minilink-addedin">New in version 1.9.0</span>
[Zabbix](https://www.zabbix.com/) is an open-source monitoring tool used for
tracking and managing the performance and availability of networks, servers,
and applications in real-time.

This hook does not do any notifications on its own. Instead, it relies on your
Zabbix instance to notify and perform escalations based on the Zabbix
configuration. The `states` defined in the configuration determine which
states will trigger the hook. The value defined in the configuration of each
state is used to populate the data of the configured Zabbix item. If none are
provided, it defaults to a lower-case string of the state.

An example configuration is shown here with all the available options.

```yaml
zabbix:
    server: http://cloud.zabbix.com/zabbix/api_jsonrpc.php
    
    username: myuser
    password: secret
    api_key: b2ecba64d8beb47fc161ae48b164cfd7104a79e8e48e6074ef5b141d8a0aeeca

    host: "borg-server"
    key: borg.status
    itemid: 55105

    start:
        value: "STARTED"
    finish:
        value: "OK"
    fail:
        value: "ERROR"
    states:
        - start
        - finish
        - fail
```

This hook requires the Zabbix server be running version 7.0+


### Authentication methods

Authentication can be accomplished via `api_key` or both `username` and
`password`. If all three are declared, only `api_key` is used.


### Items

The item to be updated can be chosen by either declaring the `itemid` or both
`host` and `key`. If all three are declared, only `itemid` is used.

Keep in mind that `host` is referring to the "Host name" on the Zabbix server
and not the "Visual name".


## Scripting borgmatic

To consume the output of borgmatic in other software, you can include an
optional `--json` flag with `create`, `repo-list`, `repo-info`, or `info` to
get the output formatted as JSON.

Note that when you specify the `--json` flag, Borg's other non-JSON output is
suppressed so as not to interfere with the captured JSON. Also note that JSON
output only shows up at the console and not in syslog.


### Latest backups

All borgmatic actions that accept an `--archive` flag allow you to specify an
archive name of `latest`. This lets you get the latest archive without having
to first run `borgmatic repo-list` manually, which can be handy in automated
scripts. Here's an example:

```bash
borgmatic info --archive latest
```
