---
title: Pushover
eleventyNavigation:
  key: • Pushover
  parent: 🚨 Monitoring
---
<span class="minilink minilink-addedin">New in version 1.9.2</span>
[Pushover](https://pushover.net) makes it easy to get real-time notifications 
on your Android, iPhone, iPad, and Desktop (Android Wear and Apple Watch, 
too!).

First, create a Pushover account and login on your mobile device. Create an
Application in your Pushover dashboard.

Then, configure borgmatic with your user's unique "User Key" found in your 
Pushover dashboard and the unique "API Token" from the created Application.

Here's a basic example:


```yaml
pushover:
    token: 7ms6TXHpTokTou2P6x4SodDeentHRa
    user: hwRwoWsXMBWwgrSecfa9EfPey55WSN
```


With this configuration, borgmatic creates a Pushover event for your service
whenever borgmatic fails, but only when any of the `create`, `prune`, `compact`,
or `check` actions are run. Note that borgmatic does not contact Pushover
when a backup starts or when it ends without error by default.

You can configure Pushover to have custom parameters declared for borgmatic's
`start`, `fail` and `finish` hooks states.

Here's a more advanced example:


```yaml
pushover:
    token: 7ms6TXHpTokTou2P6x4SodDeentHRa
    user: hwRwoWsXMBWwgrSecfa9EfPey55WSN
    start:
        message: "Backup <b>Started</b>"
        priority: -2
        title: "Backup Started"
        html: True
        ttl: 10  # Message will be deleted after 10 seconds.
    fail:
        message: "Backup <font color='#ff6961'>Failed</font>"
        priority: 2  # Requests acknowledgement for messages.
        expire: 600  # Used only for priority 2. Default is 600 seconds.
        retry: 30  # Used only for priority 2. Default is 30 seconds.
        device: "pixel8"
