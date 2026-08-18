---
title: 🔒 Credentials
eleventyNavigation:
  key: 🔒 Credentials
  parent: ⚙️  Configuration
---
<span class="minilink minilink-addedin">New in version 1.9.10</span> Several
borgmatic options support reading their values directly from an external
credential store or service. To take advantage of this feature, use `{credential
...}` syntax wherever you'd like borgmatic to read in a credential (for
supported options). In borgmatic's configuration, this looks like:

```yaml
option: "{credential type ...}"
```

... where:

 * `option` is the name of the configuration option being set 
 * `type` is the source of the credential, one of:
   * `container`: [Container secrets](https://torsion.org/borgmatic/reference/configuration/credentials/container/)
   * `file`: [File-based credentials](https://torsion.org/borgmatic/reference/configuration/credentials/file/)
   * `keepassxc`: [KeePassXC passwords](https://torsion.org/borgmatic/reference/configuration/credentials/keepassxc/)
   * `systemd`: [systemd service credentials](https://torsion.org/borgmatic/reference/configuration/credentials/systemd/)
 * "`...`" provides additional arguments specific to the selected credential
   type

For example:

```yaml
encryption_passphrase: "{credential systemd borgmatic.pw}"
```

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

For details about which options support the use of `{credential ...}` syntax,
see the [configuration
reference](https://torsion.org/borgmatic/reference/configuration/).
