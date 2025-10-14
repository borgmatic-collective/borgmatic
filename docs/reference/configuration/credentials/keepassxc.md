---
title: KeePassXC passwords
eleventyNavigation:
  key: KeePassXC
  parent: 🔒 Credentials
---
<span class="minilink minilink-addedin">New in version 1.9.11</span> borgmatic
supports reading passwords from the [KeePassXC](https://keepassxc.org/) password
manager. To use this feature, start by creating an entry in your KeePassXC
database, putting your password into the "Password" field of that entry and
making sure it's saved.

Then, you can consume that password in your borgmatic configuration file. For
instance, if the entry's title is "borgmatic" and your KeePassXC database is
located at `/etc/keys.kdbx`, do this:

```yaml
encryption_passphrase: "{credential keepassxc /etc/keys.kdbx borgmatic}"
```

But if the entry's title is multiple words like `borg pw`, you'll
need to quote it:

```yaml
encryption_passphrase: "{credential keepassxc /etc/keys.kdbx 'borg pw'}"
```

With this in place, borgmatic runs the `keepassxc-cli` command to retrieve the
passphrase on demand. But note that `keepassxc-cli` will prompt for its own
passphrase in order to unlock its database, so be prepared to enter it when
running borgmatic.

The `{credential ...}` syntax works for several different options in a borgmatic
configuration file besides just `encryption_passphrase`. For instance, the
username, password, and API token options within database and monitoring hooks
support `{credential ...}`:

```yaml
postgresql_databases:
    - name: invoices
      username: postgres
      password: "{credential keepassxc /etc/keys.kdbx database}"
```

You can also optionally override the `keepassxc-cli` command that borgmatic calls to load
passwords:

```yaml
keepassxc:
    keepassxc_cli_command: /usr/local/bin/keepassxc-cli
```
