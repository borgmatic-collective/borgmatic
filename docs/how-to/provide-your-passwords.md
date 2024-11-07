---
title: How to provide your passwords
eleventyNavigation:
  key: 🔒 Provide your passwords
  parent: How-to guides
  order: 2
---
## Providing passwords and secrets to borgmatic

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

For example, to ask the *Pass* password manager to provide the passphrase:
```yaml
encryption_passcommand: pass path/to/borg-repokey
```

### Using systemd service credentials

Borgmatic supports using encrypted [credentials](https://systemd.io/CREDENTIALS/).

Save your password as an encrypted credential to `/etc/credstore.encrypted/borgmatic.pw`, e.g.,

```
# systemd-ask-password -n | systemd-creds encrypt - /etc/credstore.encrypted/borgmatic.pw
```

Then uncomment or use the following in your configuration file:

```yaml
encryption_passcommand: "cat ${CREDENTIALS_DIRECTORY}/borgmatic.pw"
```

Note that the name `borgmatic.pw` is hardcoded in the systemd service file.

To use multiple different passwords, save them as encrypted credentials to `/etc/credstore.encrypted/borgmatic/`, e.g.,

```
# mkdir /etc/credstore.encrypted/borgmatic
# systemd-ask-password -n | systemd-creds encrypt --name=borgmatic_backupserver1 - /etc/credstore.encrypted/borgmatic/backupserver1
# systemd-ask-password -n | systemd-creds encrypt --name=borgmatic_pw2 - /etc/credstore.encrypted/borgmatic/pw2
...
```

Ensure that the file names, (e.g. `backupserver1`) match the corresponding part of
the `--name` option *after* the underscore (_), and that the part *before* 
the underscore matches the directory name (e.g. `borgmatic`).

Then, uncomment the appropriate line in the systemd service file:

```
# systemctl edit borgmatic.service
...
# Load multiple encrypted credentials.
LoadCredentialEncrypted=borgmatic:/etc/credstore.encrypted/borgmatic/
```

Finally, use the following in your configuration file:

```
encryption_passcommand: "cat ${CREDENTIALS_DIRECTORY}/borgmatic_backupserver1"
```

Adjust `borgmatic_backupserver1` according to the name given to the credential 
and the directory set in the service file.

### Environment variable interpolation

<span class="minilink minilink-addedin">New in version 1.6.4</span> borgmatic
supports interpolating arbitrary environment variables directly into option
values in your configuration file. That means you can instruct borgmatic to
pull your repository passphrase, your database passwords, or any other option
values from environment variables. For instance:

```yaml
encryption_passphrase: ${YOUR_PASSPHRASE}
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `storage:` section of your configuration.

This uses the `YOUR_PASSPHRASE` environment variable as your encryption
passphrase. Note that the `{` `}` brackets are required. `$YOUR_PASSPHRASE` by
itself will not work.

In the case of `encryption_passphrase` in particular, an alternate approach
is to use Borg's `BORG_PASSPHRASE` environment variable, which doesn't even
require setting an explicit `encryption_passphrase` value in borgmatic's
configuration file.

For [database
configuration](https://torsion.org/borgmatic/docs/how-to/backup-your-databases/),
the same approach applies. For example:

```yaml
postgresql_databases:
    - name: users
      password: ${YOUR_DATABASE_PASSWORD}
```

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> Put
this option in the `hooks:` section of your configuration.

This uses the `YOUR_DATABASE_PASSWORD` environment variable as your database
password.


#### Interpolation defaults

If you'd like to set a default for your environment variables, you can do so
with the following syntax:

```yaml
encryption_passphrase: ${YOUR_PASSPHRASE:-defaultpass}
```

Here, "`defaultpass`" is the default passphrase if the `YOUR_PASSPHRASE`
environment variable is not set. Without a default, if the environment
variable doesn't exist, borgmatic will error.


#### Disabling interpolation

To disable this environment variable interpolation feature entirely, you can
pass the `--no-environment-interpolation` flag on the command-line.

Or if you'd like to disable interpolation within a single option value, you
can escape it with a backslash. For instance, if your password is literally
`${A}@!`:

```yaml
encryption_passphrase: \${A}@!
```

## Related features

Another way to override particular options within a borgmatic configuration
file is to use a [configuration
override](https://torsion.org/borgmatic/docs/how-to/make-per-application-backups/#configuration-overrides)
on the command-line. But please be aware of the security implications of
specifying secrets on the command-line.

Additionally, borgmatic action hooks support their own [variable
interpolation](https://torsion.org/borgmatic/docs/how-to/add-preparation-and-cleanup-steps-to-backups/#variable-interpolation),
although in that case it's for particular borgmatic runtime values rather than
(only) environment variables.

Lastly, if you do want to specify your passhprase directly within borgmatic
configuration, but you'd like to keep it in a separate file from your main
configuration, you can [use a configuration include or a merge
include](https://torsion.org/borgmatic/docs/how-to/make-per-application-backups/#configuration-includes)
to pull in an external password.
