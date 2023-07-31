---
title: How to backup your databases
eleventyNavigation:
  key: 🗄️ Backup your databases
  parent: How-to guides
  order: 8
---
## Database dump hooks

If you want to backup a database, it's best practice with most database
systems to backup an exported database dump, rather than backing up your
database's internal file storage. That's because the internal storage can
change while you're reading from it. In contrast, a database dump creates a
consistent snapshot that is more suited for backups.

Fortunately, borgmatic includes built-in support for creating database dumps
prior to running backups. For example, here is everything you need to dump and
backup a couple of local PostgreSQL databases and a MySQL/MariaDB database.

```yaml
postgresql_databases:
    - name: users
    - name: orders
mysql_databases:
    - name: posts
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
these and other database options in the `hooks:` section of your
configuration.

<span class="minilink minilink-addedin">New in version 1.5.22</span> You can
also dump MongoDB databases. For example:

```yaml
mongodb_databases:
    - name: messages
```

<span class="minilink minilink-addedin">New in version 1.7.9</span>
Additionally, you can dump SQLite databases. For example:

```yaml
sqlite_databases:
    - name: mydb
      path: /var/lib/sqlite3/mydb.sqlite
```

As part of each backup, borgmatic streams a database dump for each configured
database directly to Borg, so it's included in the backup without consuming
additional disk space. (The exceptions are the PostgreSQL/MongoDB "directory"
dump formats, which can't stream and therefore do consume temporary disk
space. Additionally, prior to borgmatic 1.5.3, all database dumps consumed
temporary disk space.)

To support this, borgmatic creates temporary named pipes in `~/.borgmatic` by
default. To customize this path, set the `borgmatic_source_directory` option
in borgmatic's configuration.

Also note that using a database hook implicitly enables both the
`read_special` and `one_file_system` configuration settings (even if they're
disabled in your configuration) to support this dump and restore streaming.
See Limitations below for more on this.

Here's a more involved example that connects to remote databases:

```yaml
postgresql_databases:
    - name: users
      hostname: database1.example.org
    - name: orders
      hostname: database2.example.org
      port: 5433
      username: postgres
      password: trustsome1
      format: tar
      options: "--role=someone"
mysql_databases:
    - name: posts
      hostname: database3.example.org
      port: 3307
      username: root
      password: trustsome1
      options: "--skip-comments"
mongodb_databases:
    - name: messages
      hostname: database4.example.org
      port: 27018
      username: dbuser
      password: trustsome1
      authentication_database: mongousers
      options: "--ssl"
sqlite_databases:
    - name: mydb
      path: /var/lib/sqlite3/mydb.sqlite
```

See your [borgmatic configuration
file](https://torsion.org/borgmatic/docs/reference/configuration/) for
additional customization of the options passed to database commands (when
listing databases, restoring databases, etc.).


### All databases

If you want to dump all databases on a host, use `all` for the database name:

```yaml
postgresql_databases:
    - name: all
mysql_databases:
    - name: all
mongodb_databases:
    - name: all
```

Note that you may need to use a `username` of the `postgres` superuser for
this to work with PostgreSQL.

The SQLite hook in particular does not consider "all" a special database name.

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
these options in the `hooks:` section of your configuration.

<span class="minilink minilink-addedin">New in version 1.7.6</span> With
PostgreSQL and MySQL, you can optionally dump "all" databases to separate
files instead of one combined dump file, allowing more convenient restores of
individual databases. Enable this by specifying your desired database dump
`format`:

```yaml
postgresql_databases:
    - name: all
      format: custom
mysql_databases:
    - name: all
      format: sql
```

### Containers

If your database is running within a container and borgmatic is too, no
problem—configure borgmatic to connect to the container's name on its exposed
port. For instance:

```yaml
postgresql_databases:
    - name: users
      hostname: your-database-container-name
      port: 5433
      username: postgres
      password: trustsome1
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
these options in the `hooks:` section of your configuration.

But what if borgmatic is running on the host? You can still connect to a
database container if its ports are properly exposed to the host. For
instance, when running the database container, you can specify `--publish
127.0.0.1:5433:5432` so that it exposes the container's port 5432 to port 5433
on the host (only reachable on localhost, in this case). Or the same thing
with Docker Compose:

```yaml
services:
   your-database-container-name:
       image: postgres
       ports:
           - 127.0.0.1:5433:5432
```

And then you can connect to the database from borgmatic running on the host:

```yaml
hooks:
    postgresql_databases:
        - name: users
          hostname: 127.0.0.1
          port: 5433
          username: postgres
          password: trustsome1
```

Alter the ports in these examples to suit your particular database system.


### No source directories

<span class="minilink minilink-addedin">New in version 1.7.1</span> If you
would like to backup databases only and not source directories, you can omit
`source_directories` entirely.

<span class="minilink minilink-addedin">Prior to version 1.7.1</span> In older
versions of borgmatic, instead specify an empty `source_directories` value, as
it is a mandatory option there:

```yaml
location:
    source_directories: []

hooks:
    mysql_databases:
        - name: all
```


### External passwords

If you don't want to keep your database passwords in your borgmatic
configuration file, you can instead pass them in via [environment
variables](https://torsion.org/borgmatic/docs/how-to/provide-your-passwords/)
or command-line [configuration
overrides](https://torsion.org/borgmatic/docs/how-to/make-per-application-backups/#configuration-overrides).


### Configuration backups

An important note about this database configuration: You'll need the
configuration to be present in order for borgmatic to restore a database. So
to prepare for this situation, it's a good idea to include borgmatic's own
configuration files as part of your regular backups. That way, you can always
bring back any missing configuration files in order to restore a database.


## Supported databases

As of now, borgmatic supports PostgreSQL, MySQL/MariaDB, MongoDB, and SQLite
databases directly. But see below about general-purpose preparation and
cleanup hooks as a work-around with other database systems. Also, please [file
a ticket](https://torsion.org/borgmatic/#issues) for additional database
systems that you'd like supported.


## Database restoration

To restore a database dump from an archive, use the `borgmatic restore`
action. But the first step is to figure out which archive to restore from. A
good way to do that is to use the `rlist` action:

```bash
borgmatic rlist
```

(No borgmatic `rlist` action? Try `list` instead or upgrade borgmatic!)

That should yield output looking something like:

```text
host-2023-01-01T04:05:06.070809      Tue, 2023-01-01 04:05:06 [...]
host-2023-01-02T04:06:07.080910      Wed, 2023-01-02 04:06:07 [...]
```

Assuming that you want to restore all database dumps from the archive with the
most up-to-date files and therefore the latest timestamp, run a command like:

```bash
borgmatic restore --archive host-2023-01-02T04:06:07.080910
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
the repository to use via the `--repository` flag. This can be done either
with the repository's path or its label as configured in your borgmatic configuration file.

```bash
borgmatic restore --repository repo.borg --archive host-2023-...
```

### Restore particular databases

If you've backed up multiple databases into an archive, and you'd only like to
restore one of them, use the `--database` flag to select one or more
databases. For instance:

```bash
borgmatic restore --archive host-2023-... --database users --database orders
```

<span class="minilink minilink-addedin">New in version 1.7.6</span> You can
also restore individual databases even if you dumped them as "all"—as long as
you dumped them into separate files via use of the "format" option. See above
for more information.


### Restore all databases

To restore all databases:

```bash
borgmatic restore --archive host-2023-... --database all
```

Or omit the `--database` flag entirely:


```bash
borgmatic restore --archive host-2023-...
```

Prior to borgmatic version 1.7.6, this restores a combined "all" database
dump from the archive.

<span class="minilink minilink-addedin">New in version 1.7.6</span> Restoring
"all" databases restores each database found in the selected archive. That
includes any combined dump file named "all" and any other individual database
dumps found in the archive.


### Restore particular schemas

<span class="minilink minilink-addedin">New in version 1.7.13</span> With
PostgreSQL and MongoDB, you can limit the restore to a single schema found
within the database dump:

```bash
borgmatic restore --archive latest --database users --schema tentant1
```

### Restore to an alternate host
<span class="minilink minilink-addedin">New in version 1.7.15</span>
A database dump can be restored to a host other than the one from which it was
originally dumped. The connection parameters like the username, password, and
port can also be changed. This can be done from the command line:

```bash
borgmatic restore --archive latest --database users --hostname database2.example.org --port 5433 --username postgres --password trustsome1
```

Or from the configuration file:

```yaml
postgresql_databases:
    - name: users
        hostname: database1.example.org
        restore_hostname: database1.example.org
        restore_port: 5433
        restore_username: postgres
        restore_password: trustsome1
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
4. Because database hooks implicitly enable the `read_special` configuration,
any special files are excluded from backups (named pipes, block devices,
character devices, and sockets) to prevent hanging. Try a command like `find
/your/source/path -type b -or -type c -or -type p -or -type s` to find such
files. Common directories to exclude are `/dev` and `/run`, but that may not
be exhaustive. <span class="minilink minilink-addedin">New in version
1.7.3</span> When database hooks are enabled, borgmatic automatically excludes
special files (and symlinks to special files) that may cause Borg to hang, so
generally you no longer need to manually exclude them. There are potential
edge cases though in which applications on your system create new special files
*after* borgmatic constructs its exclude list, resulting in Borg hangs. If that
occurs, you can resort to the manual excludes described above. And to opt out
of the auto-exclude feature entirely, explicitly set `read_special` to true.


### Manual restoration

If you prefer to restore a database without the help of borgmatic, first
[extract](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/) an
archive containing a database dump.

borgmatic extracts the dump file into the *`username`*`/.borgmatic/` directory
within the extraction destination path, where *`username`* is the user that
created the backup. For example, if you created the backup with the `root`
user and you're extracting to `/tmp`, then the dump will be in
`/tmp/root/.borgmatic`.

After extraction, you can manually restore the dump file using native database
commands like `pg_restore`, `mysql`, `mongorestore`, `sqlite`, or similar.

Also see the documentation on [listing database
dumps](https://torsion.org/borgmatic/docs/how-to/inspect-your-backups/#listing-database-dumps).


## Preparation and cleanup hooks

If this database integration is too limited for needs, borgmatic also supports
general-purpose [preparation and cleanup
hooks](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/).
These hooks allows you to trigger arbitrary commands or scripts before and
after backups. So if necessary, you can use these hooks to create database
dumps with any database system.


## Troubleshooting

### PostgreSQL/MySQL authentication errors

With PostgreSQL and MySQL/MariaDB, if you're getting authentication errors
when borgmatic tries to connect to your database, a natural reaction is to
increase your borgmatic verbosity with `--verbosity 2` and go looking in the
logs. You'll notice though that your database password does not show up in the
logs. This is likely not the cause of the authentication problem unless you
mistyped your password, however; borgmatic passes your password to the
database via an environment variable that does not appear in the logs.

The cause of an authentication error is often on the database side—in the
configuration of which users are allowed to connect and how they are
authenticated. For instance, with PostgreSQL, check your
[pg_hba.conf](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html)
file for that configuration.

Additionally, MySQL/MariaDB may be picking up some of your credentials from a
defaults file like `~/.my.cnf`. If that's the case, then it's possible
MySQL/MariaDB ends up using, say, a username from borgmatic's configuration
and a password from `~/.my.cnf`. This may result in authentication errors if
this combination of credentials is not what you intend.


### MySQL table lock errors

If you encounter table lock errors during a database dump with MySQL/MariaDB,
you may need to [use a
transaction](https://dev.mysql.com/doc/refman/8.0/en/mysqldump.html#option_mysqldump_single-transaction).
You can add any additional flags to the `options:` in your database
configuration. Here's an example:

```yaml
mysql_databases:
    - name: posts
      options: "--single-transaction --quick"
```

### borgmatic hangs during backup

See Limitations above about `read_special`. You may need to exclude certain
paths with named pipes, block devices, character devices, or sockets on which
borgmatic is hanging.

Alternatively, if excluding special files is too onerous, you can create two
separate borgmatic configuration files—one for your source files and a
separate one for backing up databases. That way, the database `read_special`
option will not be active when backing up special files.

<span class="minilink minilink-addedin">New in version 1.7.3</span> See
Limitations above about borgmatic's automatic exclusion of special files to
prevent Borg hangs.
