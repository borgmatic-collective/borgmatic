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


### systemd service credentials

borgmatic supports reading encrypted [systemd
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

For specifics about which options are supported, see the
[configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/).

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

Be aware that when using this systemd `{credential ...}` feature, you may no
longer be able to run certain borgmatic actions outside of the systemd service,
as the credentials are only available from within the context of that service.
So for instance, `borgmatic list` necessarily relies on the
`encryption_passphrase` in order to access the Borg repository, but `list`
shouldn't need to load any credentials for your database or monitoring hooks.

The one exception is `borgmatic config validate`, which doesn't actually load
any credentials and should continue working anywhere.


### Container secrets

<span class="minilink minilink-addedin">New in version 1.9.11</span> When
running inside a container, borgmatic can read [Docker
secrets](https://docs.docker.com/compose/how-tos/use-secrets/) and [Podman
secrets](https://www.redhat.com/en/blog/new-podman-secrets-command). Creating
those secrets and passing them into your borgmatic container is outside the
scope of this documentation, but here's a simple example of that with [Docker
Compose](https://docs.docker.com/compose/):

```yaml
services:
  borgmatic:
    # Use the actual image name of your borgmatic container here.
    image: borgmatic:latest
    secrets:
      - borgmatic_passphrase
secrets:
  borgmatic_passphrase:
    file: /etc/borgmatic/passphrase.txt
```

This assumes there's a file on the host at `/etc/borgmatic/passphrase.txt`
containing your passphrase. Docker or Podman mounts the contents of that file
into a secret named `borgmatic_passphrase` in the borgmatic container at
`/run/secrets/`.

Once your container secret is in place, you can consume it within your borgmatic
configuration file:

```yaml
encryption_passphrase: "{credential container borgmatic_passphrase}"
```

This reads the secret securely from a file mounted at
`/run/secrets/borgmatic_passphrase` within the borgmatic container.

The `{credential ...}` syntax works for several different options in a borgmatic
configuration file besides just `encryption_passphrase`. For instance, the
username, password, and API token options within database and monitoring hooks
support `{credential ...}`:

```yaml
postgresql_databases:
    - name: invoices
      username: postgres
      password: "{credential container borgmatic_db1}"
```

For specifics about which options are supported, see the
[configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/).

You can also optionally override the `/run/secrets` directory that borgmatic reads secrets from
inside a container:

```yaml
container:
    secrets_directory: /path/to/secrets
```

But you should only need to do this for development or testing purposes.


### KeePassXC passwords

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

For specifics about which options are supported, see the
[configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/).

You can also optionally override the `keepassxc-cli` command that borgmatic calls to load
passwords:

```yaml
keepassxc:
    keepassxc_cli_command: /usr/local/bin/keepassxc-cli
```


### File-based credentials

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

For specifics about which options are supported, see the
[configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/).


### Environment variable interpolation

<span class="minilink minilink-addedin">New in version 1.6.4</span> borgmatic
supports interpolating arbitrary environment variables directly into option
values in your configuration file. That means you can instruct borgmatic to
pull your repository passphrase, your database passwords, or any other option
values from environment variables.

Be aware though that environment variables may be less secure than some of the
other approaches above for getting credentials into borgmatic. That's because
environment variables may be visible from within child processes and/or OS-level
process metadata.

Here's an example of using an environment variable from borgmatic's
configuration file:

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
