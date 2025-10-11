---
title: How to monitor your backups
eleventyNavigation:
  key: 🚨 Monitor your backups
  parent: How-to guides
  order: 6
---
Having backups is great, but they won't do you a lot of good unless you have
confidence that they're running on a regular basis. That's where monitoring
and alerting comes in.

There are several different ways you can monitor your backups and find out
whether they're succeeding. Which of these you choose to do is up to you and
your particular infrastructure:

 * **Job runner alerts**: The easiest place to start is with failure alerts from
   the [scheduled job
   runner](https://torsion.org/borgmatic/how-to/set-up-backups/#autopilot)
   (cron, systemd, etc.) that's running borgmatic. But note that if the job
   doesn't even get scheduled (e.g. due to the job runner not running), you
   probably won't get an alert at all! Still, this is a decent first line of
   defense, especially when combined with some of the other approaches below.
 * **Third-party monitoring services:** borgmatic integrates with these monitoring
   services and libraries, pinging them as backups happen. The idea is that
   you'll receive an alert when something goes wrong or when the service doesn't
   hear from borgmatic for a configured interval (if supported). While these
   services and libraries offer different features, you probably only need to
   use one of them at most. See the [monitoring configuration
   documentation](https://torsion.org/borgmatic/reference/configuration/monitoring/)
   for details.
 * **Third-party monitoring software:** You can use traditional monitoring
   software to consume borgmatic JSON output and track when the last successful
   backup occurred. See [scripting
   borgmatic](https://torsion.org/borgmatic/how-to/monitor-your-backups/#scripting-borgmatic)
   below for how to configure this.
 * **Borg hosting providers:** Some [Borg hosting
   providers](https://torsion.org/borgmatic/#hosting-providers) include
   monitoring and alerting as part of their offering. This gives you a dashboard
   to check on all of your backups, and can alert you if the service doesn't
   hear from borgmatic for a configured interval.
 * **Consistency checks:** While not strictly part of monitoring, if you want
   confidence that your backups are not only running but are restorable as well,
   you can configure particular [consistency
   checks](https://torsion.org/borgmatic/how-to/deal-with-very-large-backups/#consistency-check-configuration)
   or even script full [extract
   tests](https://torsion.org/borgmatic/how-to/extract-a-backup/).
 * **Commands run on error:** borgmatic's command hooks support running
   arbitrary commands or scripts when borgmatic itself encounters an error
   running your backups. So for instance, you can run a script to send yourself
   a text message alert. But note that if borgmatic doesn't actually run, this
   alert won't fire. See the [documentation on command hooks](https://torsion.org/borgmatic/how-to/add-preparation-and-cleanup-steps-to-backups/)
   for details.


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
