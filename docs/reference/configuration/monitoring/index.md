---
title: Monitoring
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

 * [Apprise](https://torsion.org/borgmatic/reference/configuration/monitoring/apprise/)
 * [Cronhub](https://torsion.org/borgmatic/reference/configuration/monitoring/cronhub/)
 * [Cronitor](https://torsion.org/borgmatic/reference/configuration/monitoring/cronitor/)
 * [Grafana Loki](https://torsion.org/borgmatic/reference/configuration/monitoring/loki/)
 * [Healthchecks](https://torsion.org/borgmatic/reference/configuration/monitoring/healthchecks/)
 * [ntfy](https://torsion.org/borgmatic/reference/configuration/monitoring/ntfy/)
 * [PagerDuty](https://torsion.org/borgmatic/reference/configuration/monitoring/pagerduty/)
 * [Pushover](https://torsion.org/borgmatic/reference/configuration/monitoring/pushover/)
 * [Sentry](https://torsion.org/borgmatic/reference/configuration/monitoring/sentry/)
 * [Uptime Kuma](https://torsion.org/borgmatic/reference/configuration/monitoring/uptime-kuma/)
 * [Zabbix](https://torsion.org/borgmatic/reference/configuration/monitoring/zabbix/)

