---
title: MariaDB
eleventyNavigation:
  key: MariaDB
  parent: 🗄️ Data sources
---

<span class="minilink minilink-addedin">New in version 1.8.2</span> To backup
MariaDB with borgmatic, use the `mariadb_databases:` hook instead of
`mysql_databases:` as the MariaDB hook calls native MariaDB commands instead of
the deprecated MySQL ones. For instance:

```yaml
mariadb_databases:
    - name: comments
```


## System databases

<span class="minilink minilink-addedin">New in version 2.1.6</span> When dumping
["all"
databases](https://torsion.org/borgmatic/how-to/backup-your-databases/#all-databases),
borgmatic excludes most data coming from [MariaDB system
databases](https://mariadb.com/docs/server/reference/system-tables),
because much of it is populated on MariaDB startup and thus not restorable (or
just unnecessary to backup).

The system data that borgmatic does include in these dumps are: users, roles,
grants, user-defined functions, and remote servers—all from the `mysql` system
database. This omits all other data from the `mysql` database, which includes
index and table statistics, time zones, and installed server plugins. It also
excludes the separate `information_schema`, `performance_schema`, and `sys`
system databases. This is not currently configurable.

Within a Borg archive, you can find this data stored in a dump named `mysql`—the
name of the system table this data comes from. And if you'd like to dump this
data without having to dump "all" databases, then you can configure a database
named `mysql` in your borgmatic configuration. For example:

```yaml
mariadb_databases:
    - name: mysql
```

Even in this case though, only the subset of system data described above is
included in the dump.

<span class="minilink minilink-addedin">Prior to version 2.1.6</span> Dumps of
"all" databases excluded system databases and all of their data. Additionally,
explicitly dumping `mysql` was treated like any other database—and thus wasn't
easily restorable.


## Full configuration

{% include snippet/configuration/sample.md %}

```yaml
{% include borgmatic/mariadb_databases.yaml %}
```


## Related documentation

 * [How to backup your databases](https://torsion.org/borgmatic/how-to/backup-your-databases/)
