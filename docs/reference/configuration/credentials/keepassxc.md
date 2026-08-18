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


### Custom commands

You can also optionally override the `keepassxc-cli` or `secret-tool` commands
that borgmatic call to load passwords:

```yaml
keepassxc:
    keepassxc_cli_command: /usr/local/bin/keepassxc-cli
    secret_tool_command: /usr/local/bin/secret-tool
```

Another example:

```yaml
keepassxc:
    keepassxc_cli_command: docker exec keepassxc keepassxc-cli
```

### Key file

<span class="minilink minilink-addedin">New in version 2.0.0</span>KeePassXC
supports unlocking a database with a separate [key
file](https://keepassxc.org/docs/#faq-keyfile-howto) instead of or in addition
to a password. To configure borgmatic for that, use the `key_file` option:

```yaml
keepassxc:
    key_file: /path/to/keyfile
```

<span class="minilink minilink-addedin">New in version 2.0.12</span>By default,
keepassxc-cli prompts the user for the password to unlock a database. But if you
only want to provide a key file to unlock your database and not a password, for
instance to support unattended backups, use the `ask_for_password` option:

```yaml
keepassxc:
    ask_for_password: false
    key_file: /path/to/keyfile
```

### YubiKey

<span class="minilink minilink-addedin">New in version 2.0.0</span>KeePassXC
also supports unlocking a database with the help of [a
YubiKey](https://keepassxc.org/docs/#faq-yubikey-2fa). To configure borgmatic
for that, use the `yubikey` option:

```yaml
keepassxc:
    yubikey: 1:7370001
```

The value here is the YubiKey slot number (e.g., `1` or `2`) and optional serial
number (e.g., `7370001`) used to access the KeePassXC database. Join the two
values with a colon, but omit the colon if you're leaving out the serial number.


### Secret service integration

<span class="minilink minilink-addedin">New in version 2.1.6</span> borgmatic
supports [KeePassXC's secret service
integration](https://keepassxc.org/docs/KeePassXC_UserGuide#_secret_service_integration)
that integrates with the [freedesktop secret service
API](https://specifications.freedesktop.org/secret-service/latest/) and allows
clients like borgmatic to access your passwords.

To use this feature from borgmatic, specify `secret-service` instead of a
KeePassXC database path when calling this credential hook. For instance:

```yaml
encryption_passphrase: "{credential keepassxc secret-service borgmatic}"
```

With this in place, borgmatic runs libsecret's `secret-tool` command to retrieve
the password titled "borgmatic" on demand. KeePassXC may then prompt you to
approve the password access, depending on how you've configured it.

One benefit of using the KeePassXC's secret service integration like this is
that you don't have to type a KeePassXC database passhprase (or use a keyfile)
whenever borgmatic accesses your passwords. Instead, you can configure
KeePassXC to prompt you to approve or deny each access. Or you can even
pre-approve password access to support automated borgmatic runs.
