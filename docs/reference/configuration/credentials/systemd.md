---
title: systemd service credentials
eleventyNavigation:
  key: • systemd
  parent: 🔒 Credentials
---
<span class="minilink minilink-addedin">New in version 1.9.10</span> borgmatic
supports reading encrypted [systemd
credentials](https://systemd.io/CREDENTIALS/). To use this feature, start by
saving your password as an encrypted credential to
`/etc/credstore.encrypted/borgmatic.pw`, e.g.,

```bash
systemd-ask-password -n | systemd-creds encrypt - /etc/credstore.encrypted/borgmatic.pw
```

Then use the following in your configuration file:

```yaml
encryption_passphrase: "{credential systemd borgmatic.pw}"
```

<span class="minilink minilink-addedin">Prior to version 1.9.10</span> You can
accomplish the same thing with this configuration:

```yaml
encryption_passcommand: cat ${CREDENTIALS_DIRECTORY}/borgmatic.pw
```

Note that the name `borgmatic.pw` is hardcoded in the systemd service file.

The `{credential ...}` syntax works for several different options in a borgmatic
configuration file besides just `encryption_passphrase`. For instance, the
username, password, and API token options within database and monitoring hooks
support `{credential ...}`:

```yaml
postgresql_databases:
    - name: invoices
      username: postgres
      password: "{credential systemd borgmatic_db1}"
```

To use these credentials, you'll need to modify the borgmatic systemd service
file to support loading multiple credentials (assuming you need to load more
than one or anything not named `borgmatic.pw`).

Start by saving each encrypted credentials to
`/etc/credstore.encrypted/borgmatic/`. E.g.,

```bash
mkdir /etc/credstore.encrypted/borgmatic
systemd-ask-password -n | systemd-creds encrypt --name=borgmatic_backupserver1 - /etc/credstore.encrypted/borgmatic/backupserver1
systemd-ask-password -n | systemd-creds encrypt --name=borgmatic_pw2 - /etc/credstore.encrypted/borgmatic/pw2
...
```

Ensure that the file names, (e.g. `backupserver1`) match the corresponding part
of the `--name` option *after* the underscore (_), and that the part *before*
the underscore matches the directory name (e.g. `borgmatic`).

Then, uncomment the appropriate line in the systemd service file:

```
systemctl edit borgmatic.service
...
# Load multiple encrypted credentials.
LoadCredentialEncrypted=borgmatic:/etc/credstore.encrypted/borgmatic/
```

Finally, use something like the following in your borgmatic configuration file
for each option value you'd like to load from systemd:

```yaml
encryption_passphrase: "{credential systemd borgmatic_backupserver1}"
```

<span class="minilink minilink-addedin">Prior to version 1.9.10</span> Use the
following instead, but only for the `encryption_passcommand` option and
not other options:

```yaml
encryption_passcommand: cat ${CREDENTIALS_DIRECTORY}/borgmatic_backupserver1
```

Adjust `borgmatic_backupserver1` according to the name of the credential and the
directory set in the service file.

<span class="minilink minilink-addedin">New in version 2.0.9</span> When using
the systemd `{credential ...}` feature, borgmatic loads systemd credentials even
when run outside of a systemd service. This works by falling back to calling
`systemd-creds decrypt` instead of reading credentials directly. To customize
this behavior, you can override the `systemd-creds` command and/or the
credential store directory it uses:

```yaml
systemd:
    systemd_creds_command: /usr/local/bin/systemd-creds
    encrypted_credentials_directory: /path/to/credstore.encrypted
```

<span class="minilink minilink-addedin">Prior to version 2.0.9</span> The
systemd `{credential ...}` feature did not work when run outside of a systemd
service. But depending on the borgmatic action invoked and the configuration
option where `{credential ...}` was used, you could sometimes get away without
working systemd credentials for certain actions. For instance, `borgmatic list`
doesn't connect to any databases or monitoring services, and `borgmatic config
validate` doesn't use credentials as all.
