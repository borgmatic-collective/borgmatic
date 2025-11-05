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
