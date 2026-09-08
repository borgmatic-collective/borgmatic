---
title: InfluxDB
eleventyNavigation:
  key: InfluxDB
  parent: 🗄️ Data sources
---

<span class="minilink minilink-addedin">New in version 2.1.8</span> To backup
InfluxDB with borgmatic, use the `influxdb_databases:` hook. For instance:

```yaml
influxdb_databases:
    - name: mybucket
      password: mytoken
```

This hook requires the [`influx` command-line
tool](https://docs.influxdata.com/influxdb/v2/tools/influx-cli/) from InfluxDB
2.x, as borgmatic dumps and restores with `influx backup` and `influx restore`.
Because those commands produce a directory of files rather than a single file,
this hook writes each dump to temporary disk space instead of streaming it
directly to Borg.

See below for the full set of configuration options available, including
hostname, organization, TLS settings, etc.


## InfluxDB versions

This hook supports InfluxDB 2.x only. InfluxDB 3 has no means of producing a
local database dump, so there's nothing for borgmatic to include in a backup:

 * [InfluxDB 3
   Core](https://docs.influxdata.com/influxdb3/core/admin/backup-restore/) has
   no backup or restore commands at all. Backing it up means copying its object
   store by hand in a particular order.
 * InfluxDB 3 Enterprise added [backup and
   restore](https://docs.influxdata.com/influxdb3/enterprise/admin/backup-restore/)
   in 3.11, but a backup goes to the server's own object store rather than to a
   path of your choosing, and the command returns as soon as the backup starts
   instead of when it finishes.

The 2.x `influx` command-line tool can't bridge the gap either, because its
`backup` and `restore` commands use the `/api/v2/backup` and `/api/v2/restore`
endpoints, which InfluxDB 3 doesn't implement.

Supporting InfluxDB 3 therefore calls for a separate hook that works
differently, which may come in a future version of borgmatic.


## Buckets

The `name` option is the name of the InfluxDB bucket to dump. To dump every
bucket in an instance instead, set it to `all`:

```yaml
influxdb_databases:
    - name: all
      password: mytoken
```

If you'd rather select a bucket by ID than by name, set the `bucket_id` option.
It takes precedence over the bucket named by `name` (but `name` is still used to
identify the dump within the backup, so it remains required):

```yaml
influxdb_databases:
    - name: mybucket
      bucket_id: 06fc0dfd1a97b4c1
      password: mytoken
```

Organizations work the same way: `organization_id` takes precedence over
`organization_name` when both are given.


## Authentication

The `password` option is an InfluxDB API token. It's named `password` rather
than `token` so that borgmatic's own password handling applies to it (which means
you can keep it out of your configuration file with the [`{credential ...}`
syntax](https://torsion.org/borgmatic/reference/configuration/credentials/)):

```yaml
influxdb_databases:
    - name: mybucket
      password: "{credential file /credentials/influxdb_token.txt}"
```

Alternatively, omit `password` entirely and let the `influx` command-line tool
supply the token from its own configuration, selected with the
`active_configuration` option and optionally located with `configurations_path`:

```yaml
influxdb_databases:
    - name: mybucket
      active_configuration: myconfig
```


## Restoring

By default, borgmatic restores each bucket back to the bucket and organization
it was dumped from. Use `restore_bucket` and `restore_organization` to restore
somewhere else instead, and `full_replace` to replace all data on the server
rather than merging into it.

You can also override the connection settings at restore time without editing
your configuration:

```bash
borgmatic restore --data-source mybucket --hostname influx.example.org --port 8086 --password othertoken
```


## Full configuration

{% include snippet/configuration/sample.md %}

```yaml
{% include borgmatic/influxdb_databases.yaml %}
```


## Related documentation

 * [How to backup your databases](https://torsion.org/borgmatic/how-to/backup-your-databases/)
