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
databases, streaming them directly to Borg when creating a backup. Here are the
supported databases and how to configure their borgmatic integrations:

 * [MariaDB](https://torsion.org/borgmatic/reference/configuration/data-sources/mariadb/)
 * [MongoDB](https://torsion.org/borgmatic/reference/configuration/data-sources/mongodb/)
 * [MySQL](https://torsion.org/borgmatic/reference/configuration/data-sources/mysql/)
 * [PostgreSQL](https://torsion.org/borgmatic/reference/configuration/data-sources/postgresql/)
 * [SQLite](https://torsion.org/borgmatic/reference/configuration/data-sources/sqlite/)

For supported filesystems, borgmatic takes on-demand snapshots of configured
source directories and feeds them to Borg. Here are the supported filesystems /
volume managers and how to configure their borgmatic integrations:

 * [Btrfs](https://torsion.org/borgmatic/reference/configuration/data-sources/btrfs/)
 * [LVM](https://torsion.org/borgmatic/reference/configuration/data-sources/lvm/)
 * [ZFS](https://torsion.org/borgmatic/reference/configuration/data-sources/zfs/)
