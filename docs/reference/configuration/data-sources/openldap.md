---
title: OpenLDAP
eleventyNavigation:
  key: OpenLDAP
  parent: 🗄️ Data sources
---
<span class="minilink minilink-addedin">New in version 2.1.8</span> To backup
OpenLDAP with borgmatic, use the `openldap_databases:` hook. For example:

```yaml
openldap_databases:
    - name: dc=example,dc=com
```

borgmatic dumps each configured database with `slapcat` and restores it with
`slapadd`. Both commands read and write the local `slapd` databases directly
rather than connecting over the network, so borgmatic has to run on the LDAP
server itself—and with enough permission to read those databases, which usually
means running as root.


## Suffixes instead of database names

Unlike the other database hooks, the `name` option here is an LDAP suffix (base
DN) rather than a database name, because that's how `slapcat` and `slapadd`
select a database with their `-b` flag. So list each suffix you want to backup:

```yaml
openldap_databases:
    - name: dc=example,dc=com
    - name: dc=other,dc=example,dc=com
```

This hook also doesn't accept a `name` of `all`. `slapcat` without a `-b` flag
dumps only the first configured database instead of every one of them, so
there's nothing sensible for borgmatic to map `all` onto. Giving a database the
name `all` is a validation error, so borgmatic rejects it up front rather than
partway through a backup.


## The slapd configuration database

`slapcat` and `slapadd` both need the local `slapd` configuration in order to
run, which means a dump of your data alone isn't enough to restore from. To back
up that configuration, add its suffix alongside your data suffixes:

```yaml
openldap_databases:
    - name: cn=config
    - name: dc=example,dc=com
```

`cn=config` gets dumped and restored just like any other suffix. When restoring,
restore `cn=config` first and in its own borgmatic run, so that the
configuration for your data databases is in place before you load them:

```bash
borgmatic restore --archive latest --database cn=config
borgmatic restore --archive latest --database dc=example,dc=com
```


## Restoring

`slapadd` refuses to add entries that already exist, so before you restore, stop
`slapd` and empty the directory for the database you're restoring. borgmatic
doesn't stop `slapd` or clear those directories for you, since it may not be
responsible for every database living there.

Which directory that is depends on the suffix: your data databases live
somewhere like `/var/lib/ldap`, while `cn=config` lives in the `slapd.d`
configuration directory—`/etc/ldap/slapd.d` on Debian or `/etc/openldap/slapd.d`
on Red Hat.

`slapadd` also writes its files as the user that runs it—root, typically—while
`slapd` runs as an unprivileged user like `openldap` on Debian or `ldap` on Red
Hat. If those don't match on your system, `slapd` won't be able to read what you
just restored, so change the ownership of the directory afterwards.

Here's an example of the sort of configuration that may help on some
distributions—adjust the paths and the user to match yours:

```yaml
commands:
    - before: action
      when: [restore]
      run:
          - systemctl stop slapd
    - after: action
      when: [restore]
      run:
          - chown -R openldap:openldap /var/lib/ldap
          - chown -R openldap:openldap /etc/ldap/slapd.d
          - systemctl start slapd
```

The "after" hook deliberately has no `states` option, so it runs whether or not
the restore succeeds. Otherwise a failed `slapadd` would leave `slapd` stopped.

These hooks run on every `restore` run, so if you're restoring `cn=config` and
your data in separate runs as described above, `slapd` gets stopped and started
around each of them.


## Full configuration

{% include snippet/configuration/sample.md %}

```yaml
{% include borgmatic/openldap_databases.yaml %}
```


## Related documentation

 * [How to backup your databases](https://torsion.org/borgmatic/how-to/backup-your-databases/)
