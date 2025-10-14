---
title: File-based credentials
eleventyNavigation:
  key: File
  parent: 🔒 Credentials
---
<span class="minilink minilink-addedin">New in version 1.9.11</span> borgmatic
supports reading credentials from arbitrary file paths. To use this feature,
start by writing your credential into a file that borgmatic has permission to
read. Take care not to include anything in the file other than your credential.
(borgmatic is smart enough to strip off a trailing newline though.)

You can consume that credential file in your borgmatic configuration. For
instance, if your credential file is at `/credentials/borgmatic.txt`, do this:

```yaml
encryption_passphrase: "{credential file /credentials/borgmatic.txt}"
```

With this in place, borgmatic reads the credential from the file path.

The `{credential ...}` syntax works for several different options in a borgmatic
configuration file besides just `encryption_passphrase`. For instance, the
username, password, and API token options within database and monitoring hooks
support `{credential ...}`:

```yaml
postgresql_databases:
    - name: invoices
      username: postgres
      password: "{credential file /credentials/database.txt}"
```
