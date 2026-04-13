---
title: PostgreSQL
eleventyNavigation:
  key: PostgreSQL
  parent: 🗄️ Data sources
---

<span class="minilink minilink-addedin">New in version 1.4.0</span> To backup
PostgreSQL with borgmatic, use the `postgresql_databases:` hook. For instance:

```yaml
postgresql_databases:
    - name: users
```

See below for the full set of configuration options available, including
hostname, PostgreSQL username, password, etc.


## Permissions

### Dumping

In order to dump your database as part of creating a backup, the PostgreSQL user
performing the dump needs relevant permissions. A common way to accomplish this
is to connect as the PostgreSQL superuser, usually `postgres`. However, if you'd
like to connect as a non-superuser, that user will need permissions to:

 * connect to the database
 * read tables and sequences

Here is one way to do that with PostgreSQL 14+:

```sql
GRANT CONNECT ON DATABASE example_database TO database_user;
GRANT pg_read_all_data TO database_user;
```

And here is an alternate way to accomplish something similar that limits read access
to a particular schema instead of the whole cluster. Replace "public" with the
name of the schema you're using:

```sql
GRANT CONNECT ON DATABASE example_database TO database_user;
GRANT USAGE ON SCHEMA public TO database_user;
-- Grant read privileges on all current and future tables in the schema.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO database_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO database_user;
-- Grant read privileges on all current and future indexes in the schema.
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO database_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO database_user;
```

### Restoring

If you also want this user to be able to restore your database, and you're not
restoring as the PostgreSQL superuser, then you'll need to grant write and
`ANALYZE` permissions as well. For instance:

```sql
GRANT pg_write_all_data TO database_user;
GRANT pg_maintain TO database_user;
```

Or you can perform schema-level grants if you prefer.

For more information, see the PostgreSQL documentation on [PostgreSQL predefined
roles](https://www.postgresql.org/docs/current/predefined-roles.html) and
[privileges](https://www.postgresql.org/docs/current/ddl-priv.html).


## Full configuration

{% include snippet/configuration/sample.md %}

```yaml
{% include borgmatic/postgresql_databases.yaml %}
```
