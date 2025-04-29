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
backup a couple of local PostgreSQL databases and a MySQL database.

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

<span class="minilink minilink-addedin">New in version 1.8.2</span> If you're
using MariaDB, use the MariaDB database hook instead of `mysql_databases:` as
the MariaDB hook calls native MariaDB commands instead of the deprecated MySQL
ones. For instance:

```yaml
mariadb_databases:
    - name: comments
```

As part of each backup, borgmatic streams a database dump for each configured
database directly to Borg, so it's included in the backup without consuming
additional disk space. (The exceptions are the PostgreSQL/MongoDB `directory`
dump formats, which can't stream and therefore do consume temporary disk
space. Additionally, prior to borgmatic 1.5.3, all database dumps consumed
temporary disk space.)

Also note that using a database hook implicitly enables the `read_special`
configuration option (even if it's disabled in your configuration) to support
this dump and restore streaming. See Limitations below for more on this.

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
mariadb_databases:
    - name: photos
      hostname: database3.example.org
      port: 3307
      username: root
      password: trustsome1
      options: "--skip-comments"
mysql_databases:
    - name: posts
      hostname: database4.example.org
      port: 3307
      username: root
      password: trustsome1
      options: "--skip-comments"
mongodb_databases:
    - name: messages
      hostname: database5.example.org
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


### Runtime directory

<span class="minilink minilink-addedin">New in version 1.9.0</span> To support
streaming database dumps to Borg, borgmatic uses a runtime directory for
temporary file storage, probing the following locations (in order) to find it:

 1. The `user_runtime_directory` borgmatic configuration option.
 2. The `XDG_RUNTIME_DIR` environment variable, usually `/run/user/$UID`
    (where `$UID` is the current user's ID), automatically set by PAM on Linux
    for a user with a session.
 3. <span class="minilink minilink-addedin">New in version 1.9.2</span>The
    `RUNTIME_DIRECTORY` environment variable, set by systemd if
    `RuntimeDirectory=borgmatic` is added to borgmatic's systemd service file.
 4. <span class="minilink minilink-addedin">New in version 1.9.1</span>The
    `TMPDIR` environment variable, set on macOS for a user with a session,
    among other operating systems.
 5. <span class="minilink minilink-addedin">New in version 1.9.1</span>The
    `TEMP` environment variable, set on various systems.
 6. <span class="minilink minilink-addedin">New in version 1.9.2</span>
    Hard-coded `/tmp`. <span class="minilink minilink-addedin">Prior to
    version 1.9.2</span>This was instead hard-coded to `/run/user/$UID`.

You can see the runtime directory path that borgmatic selects by running with
`--verbosity 2` and looking for "Using runtime directory" in the output.

Regardless of the runtime directory selected, borgmatic stores its files
within a `borgmatic` subdirectory of the runtime directory. Additionally, in
the case of `TMPDIR`, `TEMP`, and the hard-coded `/tmp`, borgmatic creates a
randomly named subdirectory in an effort to reduce path collisions in shared
system temporary directories.

<span class="minilink minilink-addedin">Prior to version 1.9.0</span>
borgmatic created temporary streaming database dumps within the `~/.borgmatic`
directory by default. At that time, the path was configurable by the
`borgmatic_source_directory` configuration option (now deprecated).


### All databases

If you want to dump all databases on a host, use `all` for the database name:

```yaml
postgresql_databases:
    - name: all
mariadb_databases:
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
PostgreSQL, MariaDB, and MySQL, you can optionally dump "all" databases to
separate files instead of one combined dump file, allowing more convenient
restores of individual databases. Enable this by specifying your desired
database dump `format`:

```yaml
postgresql_databases:
    - name: all
      format: custom
mariadb_databases:
    - name: all
      format: sql
mysql_databases:
    - name: all
      format: sql
```

### Database containers

If your database server is running within a container and borgmatic is too, no
problem—configure borgmatic to connect to the container's name on its exposed
port. For instance:

```yaml
postgresql_databases:
    - name: users
      hostname: your-database-server-container-name
      port: 5433
      username: postgres
      password: trustsome1
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
these options in the `hooks:` section of your configuration.


#### Database client on the host

But what if borgmatic is running on the host? You can still connect to a
database server container if its ports are properly exposed to the host. For
instance, when running the database container, you can specify `--publish
127.0.0.1:5433:5432` so that it exposes the container's port 5432 to port 5433
on the host (only reachable on localhost, in this case). Or the same thing with
Docker Compose:

```yaml
services:
   your-database-server-container-name:
       image: postgres
       ports:
           - 127.0.0.1:5433:5432
```

And then you can configure borgmatic running on the host to connect to the
database:

```yaml
postgresql_databases:
    - name: users
      hostname: 127.0.0.1
      port: 5433
      username: postgres
      password: trustsome1
```

Alter the ports in these examples to suit your particular database system.


#### Database client in a running container

Normally, borgmatic dumps a database by running a database dump command (e.g.
`pg_dump`) on the host or wherever borgmatic is running, and this command
connects to your containerized database via the given `hostname` and `port`. But
if you don't have any database dump commands installed on your host and you'd
rather use the commands inside your running database container itself, borgmatic
supports that too. For that, configure borgmatic to `exec` into your container
to run the dump command.

For instance, if using Docker and PostgreSQL, something like this might work:

```yaml
postgresql_databases:
    - name: users
      hostname: 127.0.0.1
      port: 5433
      username: postgres
      password: trustsome1
      pg_dump_command: docker exec my_pg_container pg_dump
```

... where `my_pg_container` is the name of your running database container.
Running `pg_dump` this way takes advantage of the localhost "trust"
authentication within that container. In this example, you'd also need to set
the `pg_restore_command` and `psql_command` options.

If you choose to use the `pg_dump` command within the container, and you're
using the `directory` format in particular, you'll also need to mount the
[runtime directory](#runtime-directory) from your host into the container at the
same path. Otherwise, the `directory` format dump will remain locked away inside
the database container where Borg can't read it.

For example, with Docker Compose and a runtime directory located at
`/run/user/1000`:

```yaml
services:
  db:
    image: postgres
    volumes:
      - /run/user/1000:/run/user/1000
```

And here's an example of using a MariaDB database client within a running Docker
container:

```yaml
mariadb_databases:
    - name: users
      hostname: 127.0.0.1
      username: example
      password: trustsome1
      password_transport: environment
      mariadb_dump_command: docker exec --env MYSQL_PWD my_mariadb_container mariadb-dump
```

The `password_transport: environment` option tells borgmatic to transmit the
password via environment variable instead of the default behavior of using an
anonymous pipe. The environment variable transport is potentially less secure
than the pipe, but it's necessary when the database client is running in a
container separate from borgmatic.

A similar approach can work with MySQL, using `mysql_dump_command` instead of
`mariadb_dump_command` to run `mysqldump` in a container.


#### Database client in a temporary container

Another variation: If you're running borgmatic on the host but want to spin up a
temporary `pg_dump` container whenever borgmatic dumps a database, for
instance to make use of a `pg_dump` version not present on the host, try
something like this:

```yaml
postgresql_databases:
    - name: users
      hostname: your-database-hostname
      username: postgres
      password: trustsome1
      pg_dump_command: docker run --rm --env PGPASSWORD postgres:17-alpine pg_dump
```

The `--env PGPASSWORD` is necessary here for borgmatic to provide your database
password to the temporary `pg_dump` container.

Similar command override options are available for (some of) the other
supported database types as well. See the [configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/) for
details.


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
configuration file, you can instead pass them in [from external credential
sources](https://torsion.org/borgmatic/docs/how-to/provide-your-passwords/).


### Configuration backups

An important note about this database configuration: You'll need the
configuration to be present in order for borgmatic to restore a database. So
to prepare for this situation, it's a good idea to include borgmatic's own
configuration files as part of your regular backups. That way, you can always
bring back any missing configuration files in order to restore a database.

<span class="minilink minilink-addedin">New in version 1.7.15</span> borgmatic
automatically includes configuration files in your backup. See [the
documentation on the `config bootstrap`
action](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/#extract-the-configuration-files-used-to-create-an-archive)
for more information.


## Supported databases

As of now, borgmatic supports PostgreSQL, MariaDB, MySQL, MongoDB, and SQLite
databases directly. But see below about general-purpose preparation and
cleanup hooks as a work-around with other database systems. Also, please [file
a ticket](https://torsion.org/borgmatic/#issues) for additional database
systems that you'd like supported.


## Database restoration

When you want to replace an existing database with its backed-up contents, you
can restore it with borgmatic. Note that the database must already exist;
borgmatic does not currently create a database upon restore.

To restore a database dump from an archive, use the `borgmatic restore`
action. But the first step is to figure out which archive to restore from. A
good way to do that is to use the `repo-list` action:

```bash
borgmatic repo-list
```

(No borgmatic `repo-list` action? Try `rlist` or `list` instead or upgrade
borgmatic!)

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

Or you can simplify this to:

```bash
borgmatic restore --archive latest
```

The `--archive` value is the name of the archive or archive hash to restore
from. This restores all databases dumps that borgmatic originally backed up to
that archive.

This is a destructive action! `borgmatic restore` replaces live databases by
restoring dumps from the selected archive. So be very careful when and where
you run it.


### Repository selection

If you have a single repository in your borgmatic configuration file(s), no
problem: the `restore` action figures out which repository to use.

But if you have multiple repositories configured, then you'll need to specify
the repository to use via the `--repository` flag. This can be done either
with the repository's path or its label as configured in your borgmatic
configuration file.

```bash
borgmatic restore --repository repo.borg --archive latest
```

### Restore particular databases

If you've backed up multiple databases into an archive, and you'd only like to
restore one of them, use the `--database` flag to select one or more
databases. For instance:

```bash
borgmatic restore --archive latest --database users --database orders
```

<span class="minilink minilink-addedin">New in version 1.7.6</span> You can
also restore individual databases even if you dumped them as "all"—as long as
you dumped them into separate files via use of the "format" option. See above
for more information.

### Restore databases sharing a name

<span class="minilink minilink-addedin">New in version 1.9.5</span> If you've
backed up multiple databases that happen to share the same name but different
hostnames, ports, or hooks, you can include additional flags to disambiguate
which database you'd like to restore. For instance, let's say you've backed up
the following configured databases:

```yaml
postgresql_databases:
    - name: users
      hostname: host1.example.org
    - name: users
      hostname: host2.example.org
```

... then you can run the following command to restore only one of them:

```bash
borgmatic restore --archive latest --database users --original-hostname host1.example.org
```

This selects a `users` database to restore, but only if it originally came
from the host `host1.example.org`. This command won't restore `users`
databases from any other hosts.

Here's another example configuration:

```yaml
postgresql_databases:
    - name: users
      hostname: example.org
      port: 5433
    - name: users
      hostname: example.org
      port: 5434
```

And a command to restore just one of the databases:

```bash
borgmatic restore --archive latest --database users --original-port 5433
```

That restores a `users` database only if it originally came from port `5433`
*and* if that port is in borgmatic's configuration, e.g. `port: 5433`.

Finally, check out this configuration:

```yaml
postgresql_databases:
    - name: users
      hostname: example.org
mariadb_databases:
    - name: users
      hostname: example.org
```

And to select just one of the databases to restore:

```bash
borgmatic restore --archive latest --database users --hook postgresql
```

That restores a `users` database only if it was dumped using the
`postgresql_databases:` data source hook. This command won't restore `users`
databases that were dumped using other hooks.

Note that these flags don't change the hostname or port to which the database
is actually restored. For that, see below about restoring to an alternate
host.


### Restore all databases

To restore all databases:

```bash
borgmatic restore --archive latest --database all
```

Or omit the `--database` flag entirely:


```bash
borgmatic restore --archive latest
```

<span class="minilink minilink-addedin">New in version 1.7.6</span> Restoring
"all" databases restores each database found in the selected archive. That
includes any combined dump file named "all" and any other individual database
dumps found in the archive. Prior to borgmatic version 1.7.6, restoring "all"
only restored a combined "all" database dump from the archive.


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

### Manual restoration

If you prefer to restore a database without the help of borgmatic, first
[extract](https://torsion.org/borgmatic/docs/how-to/extract-a-backup/) an
archive containing a database dump.

borgmatic extracts the dump file into the `borgmatic/` directory within the
extraction destination path. For example, if you're extracting to `/tmp`, then
the dump will be in `/tmp/borgmatic/`.

<span class="minilink minilink-addedin">Prior to version 1.9.0</span> borgmatic
extracted the dump file into the *`username`*`/.borgmatic/` directory within the
extraction destination path, where *`username`* is the user that created the
backup. For example, if you created the backup with the `root` user and you're
extracting to `/tmp`, then the dump will be in `/tmp/root/.borgmatic`.

After extraction, you can manually restore the dump file using native database
commands like `pg_restore`, `mysql`, `mongorestore`, `sqlite`, or similar.

Also see the documentation on [listing database
dumps](https://torsion.org/borgmatic/docs/how-to/inspect-your-backups/#listing-database-dumps).


## Limitations

There are a few important limitations with borgmatic's current database
hooks that you should know about:

1. When database hooks are enabled, borgmatic instructs Borg to consume
special files (via `--read-special`) to support database dump
streaming—regardless of the value of your `read_special` configuration option.
And because this can cause Borg to hang, borgmatic also automatically excludes
special files (and symlinks to them) that Borg may get stuck on. Even so,
there are still potential edge cases in which applications on your system
create new special files *after* borgmatic constructs its exclude list,
resulting in Borg hangs. If that occurs, you can resort to manually excluding
those files. And if you explicitly set the `read_special` option to `true`,
borgmatic will opt you out of the auto-exclude feature entirely, but will
still instruct Borg to consume special files—and you will be on your own to
exclude them. <span class="minilink minilink-addedin">Prior to version
1.7.3</span>Special files were not auto-excluded, and you were responsible for
excluding them yourself. Common directories to exclude are `/dev` and `/run`,
but that may not be exhaustive.
2. <span class="minilink minilink-addedin">Prior to version 1.9.5</span>
borgmatic did not support backing up or restoring multiple databases that
shared the exact same name on different hosts or with different ports.
3. <span class="minilink minilink-addedin">Prior to version 1.9.0</span>
Database hooks also implicitly enabled the `one_file_system` option, which
meant Borg wouldn't cross filesystem boundaries when looking for files to
backup. When borgmatic was running in a container, this often required a
work-around to explicitly add each mounted backup volume to
`source_directories` instead of relying on Borg to include them implicitly via
a parent directory. But as of borgmatic 1.9.0, `one_file_system` is no longer
auto-enabled and such work-arounds aren't necessary.
4. <span class="minilink minilink-addedin">Prior to version 1.9.0</span> You
must restore as the same Unix user that created the archive containing the
database dump. That's because the user's home directory path is encoded into
the path of the database dump within the archive.
5. <span class="minilink minilink-addedin">Prior to version 1.7.15</span> As
mentioned above, borgmatic can only restore a database that's defined in
borgmatic's own configuration file. So include your configuration files in
backups to avoid getting caught without a way to restore a database. But
starting from version 1.7.15, borgmatic includes your configuration files
automatically.


## Preparation and cleanup hooks

If this database integration is too limited for needs, borgmatic also supports
general-purpose [preparation and cleanup
hooks](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/).
These hooks allows you to trigger arbitrary commands or scripts before and
after backups. So if necessary, you can use these hooks to create database
dumps with any database system.


## Troubleshooting

### Authentication errors

With PostgreSQL, MariaDB, and MySQL, if you're getting authentication errors
when borgmatic tries to connect to your database, a natural reaction is to
increase your borgmatic verbosity with `--verbosity 2` and go looking in the
logs. You'll notice though that your database password does not show up in the
logs. But this is likely not the cause of the authentication problem unless you
mistyped your password; borgmatic passes your password to the database via an
environment variable or anonymous pipe, so the password does not appear in the
logs.

The cause of an authentication error is often on the database side—in the
configuration of which users are allowed to connect and how they are
authenticated. For instance, with PostgreSQL, check your
[pg_hba.conf](https://www.postgresql.org/docs/current/auth-pg-hba-conf.html)
file for that configuration.

Additionally, MariaDB or MySQL may be picking up some of your credentials from
a defaults file like `~/mariadb.cnf` or `~/.my.cnf`. If that's the case, then
it's possible MariaDB or MySQL end up using, say, a username from borgmatic's
configuration and a password from `~/mariadb.cnf` or `~/.my.cnf`. This may
result in authentication errors if this combination of credentials is not what
you intend.


### MariaDB or MySQL table lock errors

If you encounter table lock errors during a database dump with MariaDB or
MySQL, you may need to [use a
transaction](https://mariadb.com/docs/skysql-dbaas/ref/mdb/cli/mariadb-dump/single-transaction/).
You can add any additional flags to the `options:` in your database
configuration. Here's an example with MariaDB:

```yaml
mariadb_databases:
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
