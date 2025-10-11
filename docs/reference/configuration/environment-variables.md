---
title: Environment variables
eleventyNavigation:
  key: 💲 Environment variables
  parent: ⚙️  Configuration
---
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
configuration](https://torsion.org/borgmatic/how-to/backup-your-databases/),
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


### Interpolation defaults

If you'd like to set a default for your environment variables, you can do so
with the following syntax:

```yaml
encryption_passphrase: ${YOUR_PASSPHRASE:-defaultpass}
```

Here, "`defaultpass`" is the default passphrase if the `YOUR_PASSPHRASE`
environment variable is not set. Without a default, if the environment
variable doesn't exist, borgmatic will error.


### Disabling interpolation

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
override](https://torsion.org/borgmatic/reference/configuration/overrides/)
on the command-line. But please be aware of the security implications of
specifying secrets on the command-line.

Additionally, borgmatic action hooks support their own [variable
interpolation](https://torsion.org/borgmatic/how-to/add-preparation-and-cleanup-steps-to-backups/#variable-interpolation),
although in that case it's for particular borgmatic runtime values rather than
(only) environment variables.
