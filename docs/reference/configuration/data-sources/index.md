---
title: Data sources
eleventyNavigation:
  key: 🗄️ Data sources
  parent: ⚙️  Configuration
---
Data sources are built-in borgmatic integrations that, instead of backing up
plain filesystem data, can pull data directly from database servers and
filesystem snapshots.

In the case of supported database systems, borgmatic dumps your configured
databases, streaming them directly to Borg when creating a backup. And for
supported filesystems / volume managers, borgmatic takes on-demand snapshots of
configured source directories and feeds them to Borg.

Here are the supported data sources and how to configure their borgmatic
integrations:

{{ collections.all | eleventyNavigation: "🗄️ Data sources" | eleventyNavigationToHtml | replace: 'href="/reference/', 'href="/borgmatic/reference/' }}
