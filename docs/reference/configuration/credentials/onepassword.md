---
title: 1Password CLI credentials
eleventyNavigation:
  key: 1Password CLI
  parent: 🔒 Credentials
---
<span class="minilink minilink-addedin">New in version 2.1.8</span> borgmatic
supports reading secrets from [1Password](https://1password.com/) via the [1Password
CLI](https://developer.1password.com/docs/cli/). To use this feature, start by
saving your secret in 1Password and noting its [secret
reference](https://developer.1password.com/docs/cli/secret-references) of the
form `op://vault/item/[section/]field`.

Then use the following in your configuration file:

```yaml
encryption_passphrase: "{credential onepassword op://vault-name/item-name/field-name}"
```

With this in place, borgmatic runs the `op read` command to retrieve the secret
on demand. But note that `op read` will require you to be authenticated to your
1Password account, so be prepared to run `op signin` before running borgmatic, or
to have a [service
account](https://developer.1password.com/docs/service-accounts/) configured.

The `{credential ...}` syntax works for several different options in a borgmatic
configuration file besides just `encryption_passphrase`. For instance, the
username, password, and API token options within database and monitoring hooks
support `{credential ...}`:

```yaml
postgresql_databases:
    - name: invoices
      username: postgres
      password: "{credential onepassword op://vault-name/db/password}"
```


### Custom command

You can also optionally override the `op` command that borgmatic calls to load
secrets:

```yaml
onepassword:
    op_command: /usr/local/bin/op
```

Another example:

```yaml
onepassword:
    op_command: op --account my.1password.com
```
