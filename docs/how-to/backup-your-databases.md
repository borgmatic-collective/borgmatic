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
backup a couple of local PostgreSQL databases:

```yaml
hooks:
    postgresql_databases:
        - name: users
        - name: orders
```

Prior to each backup, borgmatic dumps each configured database to a file
(located in `~/.borgmatic/`) and includes it in the backup. After the backup
completes, borgmatic removes the database dump files to recover disk space.

Here's a more involved example that connects to a remote database:

```yaml
hooks:
    postgresql_databases:
        - name: users
          hostname: database.example.org
          port: 5433
          username: dbuser
          password: trustsome1
          format: tar
          options: "--role=someone"
```

If you want to dump all databases on a host, use `all` for the database name:

```yaml
hooks:
    postgresql_databases:
        - name: all
```

Note that you may need to use a `username` of the `postgres` superuser for
this to work.

## Supported databases

As of now, borgmatic only supports PostgreSQL databases directly. But see
below about general-purpose preparation and cleanup hooks as a work-around
with other database systems. Also, please [file a
ticket](https://torsion.org/borgmatic/#issues) for additional database systems
that you'd like supported.

## Database restoration

borgmatic does not yet perform integrated database restoration when you
[restore a backup](http://localhost:8080/docs/how-to/restore-a-backup/), but
that feature is coming in a future release. In the meantime, you can restore
a database manually after restoring a dump file in the `~/.borgmatic` path.

## Preparation and cleanup hooks

If this database integration is too limited for needs, borgmatic also supports
general-purpose [preparation and cleanup
hooks](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/).
These hooks allows you to trigger arbitrary commands or scripts before and
after backups. So if necessary, you can use these hooks to create database
dumps with any database system.

## Related documentation

 * [Set up backups with borgmatic](https://torsion.org/borgmatic/docs/how-to/set-up-backups/)
 * [Add preparation and cleanup steps to backups](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/)
 * [Inspect your backups](https://torsion.org/borgmatic/docs/how-to/inspect-your-backups/)
 * [Restore a backup](http://localhost:8080/docs/how-to/restore-a-backup/)
