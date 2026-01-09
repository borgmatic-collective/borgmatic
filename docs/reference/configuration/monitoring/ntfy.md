---
title: ntfy
eleventyNavigation:
  key: ntfy
  parent: 🚨 Monitoring
---
<span class="minilink minilink-addedin">New in version 1.6.3</span>
[ntfy](https://ntfy.sh) is a free, simple, service (either cloud-hosted or
self-hosted) which offers simple pub/sub push notifications to multiple
platforms including [web](https://ntfy.sh/stats),
[Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy) and
[iOS](https://apps.apple.com/us/app/ntfy/id1625396347).

Since push notifications for regular events might soon become quite annoying,
this hook only fires on any errors by default in order to instantly alert you
to issues. The `states` list can override this. Each state can have its own
custom messages, priorities and tags or, if none are provided, will use the
default.

Here's a basic configuration that notifies on failure:

```yaml
ntfy:
    topic: my-unique-topic
    server: https://ntfy.my-domain.com
    username: myuser
    password: secret

    fail:
        title: A borgmatic backup failed
        message: You should probably fix it
        tags: borgmatic,-1,skull
        priority: max
    states:
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


### Full configuration

{% include snippet/configuration/sample.md %}

The options here include
[priorities](https://ntfy.sh/docs/publish/#message-priority) and
[tags](https://ntfy.sh/docs/publish/#tags-emojis).

```yaml
{% include borgmatic/ntfy.yaml %}
```
