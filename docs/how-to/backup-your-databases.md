---
title: How to backup your databases
---
## Database dump hooks

If you want to backup a database, it's best practice with most database
systems to backup an exported database dump, rather than backing up your
database's internal file storage. That's because the internal storage can
change while you're reading from it. In contrast, a database dump creates a
consistent snapshot that is more suited for backups.

Fortunately, borgmatic includes built-in support for creating database dumps
prior to running backups. For example, here is everything you need to dump and
backup a couple of local PostgreSQL databases and a MySQL/MariaDB database:

```yaml
hooks:
    postgresql_databases:
        - name: users
        - name: orders
    mysql_databases:
        - name: posts
```

As part of each backup, borgmatic streams a database dump for each configured
database directly to Borg, so it's included in the backup without consuming
additional disk space. (The one exception is PostgreSQL's "directory" dump
format, which can't stream and therefore does consume temporary disk space.)

To support this, borgmatic creates temporary named pipes in `~/.borgmatic` by
default. To customize this path, set the `borgmatic_source_directory` option
in the `location` section of borgmatic's configuration.

Here's a more involved example that connects to remote databases:

```yaml
hooks:
    postgresql_databases:
        - name: users
          hostname: database1.example.org
          port: 5433
          username: postgres
          password: trustsome1
          format: tar
          options: "--role=someone"
    mysql_databases:
        - name: posts
          hostname: database2.example.org
          port: 3307
          username: root
          password: trustsome1
          options: "--skip-comments"
```

If you want to dump all databases on a host, use `all` for the database name:

```yaml
hooks:
    postgresql_databases:
        - name: all
    mysql_databases:
        - name: all
```

Note that you may need to use a `username` of the `postgres` superuser for
this to work with PostgreSQL.


### Configuration backups

An important note about this database configuration: You'll need the
configuration to be present in order for borgmatic to restore a database. So
to prepare for this situation, it's a good idea to include borgmatic's own
configuration files as part of your regular backups. That way, you can always
bring back any missing configuration files in order to restore a database.


## Supported databases

As of now, borgmatic supports PostgreSQL and MySQL/MariaDB databases
directly. But see below about general-purpose preparation and cleanup hooks as
a work-around with other database systems. Also, please [file a
ticket](https://torsion.org/borgmatic/#issues) for additional database systems
that you'd like supported.


## Database restoration

To restore a database dump from an archive, use the `borgmatic restore`
action. But the first step is to figure out which archive to restore from. A
good way to do that is to use the `list` action:

```bash
borgmatic list
```

(No borgmatic `list` action? Try the old-style `--list`, or upgrade
borgmatic!)

That should yield output looking something like:

```text
host-2019-01-01T04:05:06.070809      Tue, 2019-01-01 04:05:06 [...]
host-2019-01-02T04:06:07.080910      Wed, 2019-01-02 04:06:07 [...]
```

Assuming that you want to restore all database dumps from the archive with the
most up-to-date files and therefore the latest timestamp, run a command like:

```bash
borgmatic restore --archive host-2019-01-02T04:06:07.080910
```

(No borgmatic `restore` action? Upgrade borgmatic!)

With newer versions of borgmatic, you can simplify this to:

```bash
borgmatic restore --archive latest
```

The `--archive` value is the name of the archive to restore from. This
restores all databases dumps that borgmatic originally backed up to that
archive.

This is a destructive action! `borgmatic restore` replaces live databases by
restoring dumps from the selected archive. So be very careful when and where
you run it.


### Repository selection

If you have a single repository in your borgmatic configuration file(s), no
problem: the `restore` action figures out which repository to use.

But if you have multiple repositories configured, then you'll need to specify
the repository path containing the archive to restore. Here's an example:

```bash
borgmatic restore --repository repo.borg --archive host-2019-...
```

### Restore particular databases

If you've backed up multiple databases into an archive, and you'd only like to
restore one of them, use the `--database` flag to select one or more
databases. For instance:

```bash
borgmatic restore --archive host-2019-... --database users
```

### Limitations

There are a few important limitations with borgmatic's current database
restoration feature that you should know about:

1. You must restore as the same Unix user that created the archive containing
the database dump. That's because the user's home directory path is encoded
into the path of the database dump within the archive.
2. As mentioned above, borgmatic can only restore a database that's defined in
borgmatic's own configuration file. So include your configuration file in
backups to avoid getting caught without a way to restore a database.
3. borgmatic does not currently support backing up or restoring multiple
databases that share the exact same name on different hosts.


### Manual restoration

If you prefer to restore a database without the help of borgmatic, first
[extract](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/) an
archive containing a database dump, and then manually restore the dump file
found within the extracted `~/.borgmatic/` path (e.g. with `pg_restore` or
`mysql` commands).


## Preparation and cleanup hooks

If this database integration is too limited for needs, borgmatic also supports
general-purpose [preparation and cleanup
hooks](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/).
These hooks allows you to trigger arbitrary commands or scripts before and
after backups. So if necessary, you can use these hooks to create database
dumps with any database system.


## Troubleshooting

### MySQL table lock errors

If you encounter table lock errors during a database dump with MySQL/MariaDB,
you may need to [use a
transaction](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html#option_mysqldump_single-transaction).
You can add any additional flags to the `options:` in your database
configuration. Here's an example:

```yaml
hooks:
    mysql_databases:
        - name: posts
          options: "--single-transaction --quick"
```


## Related documentation

 * [Set up backups with borgmatic](https://torsion.org/borgmatic/docs/how-to/set-up-backups/)
 * [Add preparation and cleanup steps to backups](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/)
 * [Inspect your backups](https://torsion.org/borgmatic/docs/how-to/inspect-your-backups/)
 * [Extract a backup](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/)
