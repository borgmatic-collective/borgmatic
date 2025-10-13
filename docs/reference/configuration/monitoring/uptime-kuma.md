---
title: Uptime Kuma
eleventyNavigation:
  key: • Uptime Kuma
  parent: 🚨 Monitoring
---
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


### Full configuration

```yaml
{% include borgmatic/uptime_kuma.yaml %}
```
