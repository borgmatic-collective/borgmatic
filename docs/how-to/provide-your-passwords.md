---
title: 🔒 How to provide your passwords
eleventyNavigation:
  key: 🔒 Provide your passwords
  parent: How-to guides
  order: 2
---
If you want to use a Borg repository passphrase or database passwords with
borgmatic, you can set them directly in your borgmatic configuration file,
treating those secrets like any other option value. For instance, you can
specify your Borg passhprase with:

```yaml
encryption_passphrase: yourpassphrase
```

But if you'd rather store them outside of borgmatic, whether for convenience
or security reasons, read on.


### Delegating to another application

borgmatic supports calling another application such as a password manager to 
obtain the Borg passphrase to a repository.

For example, to ask the [Pass](https://www.passwordstore.org/) password manager
to provide the passphrase:

```yaml
encryption_passcommand: pass path/to/borg-passphrase
```

<span class="minilink minilink-addedin">New in version 1.9.9</span> Instead of
letting Borg run the passcommand—potentially multiple times since borgmatic runs
Borg multiple times—borgmatic now runs the passcommand itself and passes the
resulting passphrase securely to Borg via an anonymous pipe. This means you
should only ever get prompted for your password manager's passphrase at most
once per borgmatic run.


<a id="systemd-service-credentials"></a>
<a id="container-secrets"></a>
<a id="keepassxc-passwords"></a>
<a id="file-based-credentials"></a>


### Using external credentials

<span class="minilink minilink-addedin">New in version 1.9.10</span> Several
borgmatic options support reading their values directly from an external
credential store or service. See the [credentials
documentation](https://torsion.org/borgmatic/reference/configuration/credentials/)
for details.


<a id="environment-variable-interpolation"></a>


### Using environment variables

Another way to get passwords into your configuration file is by [interpolating
arbitrary environment
variables](https://torsion.org/borgmatic/reference/configuration/environment-variables/)
directly into option values.
