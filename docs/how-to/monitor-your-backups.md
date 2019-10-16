---
title: How to monitor your backups
---

## Monitoring and alerting

Having backups is great, but they won't do you a lot of good unless you have
confidence that they're running on a regular basis. That's where monitoring
and alerting comes in.

There are several different ways you can monitor your backups and find out
whether they're succeeding. Which of these you choose to do is up to you and
your particular infrastructure:

1. **Job runner alerts**: The easiest place to start is with failure alerts
from the [scheduled job
runner](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#autopilot) (cron,
systemd, etc.) that's running borgmatic. But note that if the job doesn't even
get scheduled (e.g. due to the job runner not running), you probably won't get
an alert at all! Still, this is a decent first line of defense, especially
when combined with some of the other approaches below.
2. **borgmatic error hooks**: The `on_error` hook allows you to run an arbitrary
command or script when borgmatic itself encounters an error running your
backups. So for instance, you can run a script to send yourself a text message
alert. But note that if borgmatic doesn't actually run, this alert won't fire.
See [error
hooks](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#error-hooks)
below for how to configure this.
4. **borgmatic Healthchecks hook**: This feature integrates with the
[Healthchecks](https://healthchecks.io/) service, and pings Healthchecks
whenever borgmatic runs. That way, Healthchecks can alert you when something
goes wrong or it doesn't hear from borgmatic for a configured interval. See
[Healthchecks
hook](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#healthchecks-hook)
below for how to configure this.
3. **Third-party monitoring software**: You can use traditional monitoring
software to consume borgmatic JSON output and track when the last
successful backup occurred. See [scripting
borgmatic](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/#scripting-borgmatic)
below for how to configure this.
5. **Borg hosting providers**: Most [Borg hosting
providers](https://torsion.org/borgmatic/#hosting-providers) include
monitoring and alerting as part of their offering. This gives you a dashboard
to check on all of your backups, and can alert you if the service doesn't hear
from borgmatic for a configured interval.
6. **borgmatic consistency checks**: While not strictly part of monitoring, if you
really want confidence that your backups are not only running but are
restorable as well, you can configure particular [consistency
checks](https://torsion.org/borgmatic/docs/how-to/deal-with-very-large-backups/#consistency-check-configuration)
or even script full [restore
tests](https://torsion.org/borgmatic/docs/how-to/restore-a-backup/).


## Error hooks

When an error occurs during a backup, borgmatic can run configurable shell
commands to fire off custom error notifications or take other actions, so you
can get alerted as soon as something goes wrong. Here's a not-so-useful
example:

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

In this example, when the error occurs, borgmatic interpolates a few runtime
values into the hook command: the borgmatic configuration filename, and the
path of the repository. Here's the full set of supported variables you can use
here:

 * `configuration_filename`: borgmatic configuration filename in which the
   error occurred
 * `repository`: path of the repository in which the error occurred (may be
   blank if the error occurs in a hook)
 * `error`: the error message itself
 * `output`: output of the command that failed (may be blank if an error
   occurred without running a command)

Note that borgmatic does not run `on_error` hooks if an error occurs within a
`before_everything` or `after_everything` hook. For more about hooks, see the
[borgmatic hooks
documentation](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups.md),
especially the security information.


## Healthchecks hook

[Healthchecks](https://healthchecks.io/) is a service that provides "instant
alerts when your cron jobs fail silently", and borgmatic has built-in
integration with it. Once you create a Healthchecks account and project on
their site, all you need to do is configure borgmatic with the unique "Ping
URL" for your project. Here's an example:


```yaml
hooks:
    healthchecks: https://hc-ping.com/addffa72-da17-40ae-be9c-ff591afb942a
```

With this hook in place, borgmatic will ping your Healthchecks project when a
backup begins, ends, or errors. Then you can configure Healthchecks to notify
you by a [variety of
mechanisms](https://healthchecks.io/#welcome-integrations) when backups fail
or it doesn't hear from borgmatic for a certain period of time.


## Scripting borgmatic

To consume the output of borgmatic in other software, you can include an
optional `--json` flag with `create`, `list`, or `info` to get the output
formatted as JSON.

Note that when you specify the `--json` flag, Borg's other non-JSON output is
suppressed so as not to interfere with the captured JSON. Also note that JSON
output only shows up at the console, and not in syslog.


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


## Related documentation

 * [Set up backups with borgmatic](https://torsion.org/borgmatic/docs/how-to/set-up-backups.md)
 * [Inspect your backups](https://torsion.org/borgmatic/docs/how-to/inspect-your-backups.md)
 * [Add preparation and cleanup steps to backups](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups.md)
 * [Restore a backup](https://torsion.org/borgmatic/docs/how-to/restore-a-backup.md)
 * [Develop on borgmatic](https://torsion.org/borgmatic/docs/how-to/develop-on-borgmatic.md)
