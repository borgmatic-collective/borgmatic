---
title: 🚨 Monitoring
eleventyNavigation:
  key: 🚨 Monitoring
  parent: ⚙️  Configuration
---
borgmatic integrates with third-party monitoring services and libraries, pinging
them as backups happen. The idea is that you'll receive an alert when something
goes wrong or when the service doesn't hear from borgmatic for a configured
interval (if supported). While these services and libraries offer different
features, you probably only need to use one of them at most. See their
documentation for configuration information:

{{ collections.all | eleventyNavigation: "🚨 Monitoring" | eleventyNavigationToHtml | replace: 'href="/reference/', 'href="/borgmatic/reference/' }}

## Per-repository monitoring

<span class="minilink minilink-addedin">New in version 2.2.1</span> By default, you configure a monitoring integration at the top level of your configuration. borgmatic then pings it once before the actions for all of your repositories begin and once after they have all finished or failed. With multiple repositories, a single monitoring check represents the whole run.

If you'd rather have separate monitoring for each repository, put the integration's options under that repository instead:

```yaml
repositories:
    - path: ssh://user@one.example.org/./repo.borg
      label: one
      healthchecks:
          ping_url: https://hc-ping.com/uuid-for-one

    - path: ssh://user@two.example.org/./repo.borg
      label: two
      healthchecks:
          ping_url: https://hc-ping.com/uuid-for-two
```

This works for all of the monitoring integrations listed above. Specify each integration's complete configuration under the repository.

With this configuration, borgmatic pings each repository's monitoring endpoint independently: a start ping before it processes that repository and a finish or fail ping afterward. If one repository fails, only its own check reports the failure, and borgmatic continues with the remaining repositories. If you've configured `retries`, borgmatic retries a failing repository within the same run, so you still get just one start ping and one finish or fail ping per repository.

A few things to keep in mind:

 * Monitoring configured at the top level behaves as before: one start ping before all repositories and one finish or fail ping after all of them. If any repository failed, the top-level integration reports a failure.
 * If you configure monitoring at both levels, the two apply independently. The top-level integration reports on the whole run and a repository's integration only on that repository.
 * A repository without monitoring configuration of its own doesn't inherit the top-level monitoring configuration. Its own processing isn't pinged separately.
 * The monitoring options of a repository are not merged with top-level monitoring options. Everything an integration needs must be set under the repository.
 * This is different from other repository-specific options, which override the corresponding top-level option for that repository.
