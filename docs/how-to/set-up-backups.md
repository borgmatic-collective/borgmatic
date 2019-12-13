---
title: How to set up backups with borgmatic
---
## Installation

First, [install
Borg](https://borgbackup.readthedocs.io/en/stable/installation.html), at least
version 1.1.

Then, download and install borgmatic by running the following command:

```bash
sudo pip3 install --user --upgrade borgmatic
```

This is a [recommended user site
installation](https://packaging.python.org/tutorials/installing-packages/#installing-to-the-user-site).
You will need to ensure that `/root/.local/bin` is available on your `$PATH`
so
that the borgmatic executable is available. For instance, adding this to
root's `~/.profile` or `~/.bash_profile` may do the trick:

```bash
export PATH="$PATH:~/.local/bin"
```

Note that your pip binary may have a different name than "pip3". Make sure
you're using Python 3, as borgmatic does not support Python 2.

### Other ways to install

Along with the above process, you have several other options for installing
borgmatic:

 * [Docker image with scheduled backups](https://hub.docker.com/r/b3vis/borgmatic/)
 * [Docker base image](https://hub.docker.com/r/monachus/borgmatic/)
 * [Debian](https://tracker.debian.org/pkg/borgmatic)
 * [Ubuntu](https://launchpad.net/ubuntu/+source/borgmatic)
 * [Fedora official](https://bodhi.fedoraproject.org/updates/?search=borgmatic)
 * [Fedora unofficial](https://copr.fedorainfracloud.org/coprs/heffer/borgmatic/)
 * [Arch Linux](https://www.archlinux.org/packages/community/any/borgmatic/)
 * [OpenBSD](http://ports.su/sysutils/borgmatic)
 * [openSUSE](https://software.opensuse.org/package/borgmatic)
 * [stand-alone binary](https://github.com/cmarquardt/borgmatic-binary)
 * [virtualenv](https://virtualenv.pypa.io/en/stable/)


## Hosting providers

Need somewhere to store your encrypted offsite backups? The following hosting
providers include specific support for Borg/borgmatic. Using these links and
services helps support borgmatic development and hosting. (These are referral
links, but without any tracking scripts or cookies.)

<ul>
 <li class="referral"><a href="https://www.rsync.net/cgi-bin/borg.cgi?campaign=borg&adgroup=borgmatic">rsync.net</a>: Cloud Storage provider with full support for borg and any other SSH/SFTP tool</li>
 <li class="referral"><a href="https://www.borgbase.com/?utm_source=borgmatic">BorgBase</a>: Borg hosting service with support for monitoring, 2FA, and append-only repos</li>
</ul>

## Configuration

After you install borgmatic, generate a sample configuration file:

```bash
sudo generate-borgmatic-config
```

If that command is not found, then it may be installed in a location that's
not in your system `PATH` (see above). Try looking in `~/.local/bin/`.

This generates a sample configuration file at /etc/borgmatic/config.yaml (by
default). You should edit the file to suit your needs, as the values are
representative. All options are optional except where indicated, so feel free
to ignore anything you don't need.

Note that the configuration file is organized into distinct sections, each
with a section name like `location:` or `storage:`. So take care that if you
uncomment a particular option, also uncomment its containing section name, or
else borgmatic won't recognize the option. Also be sure to use spaces rather
than tabs for indentation; YAML does not allow tabs.

You can also get the same sample configuration file from the [configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/), the
authoritative set of all configuration options. This is handy if borgmatic has
added new options
since you originally created your configuration file. Also check out how to
[upgrade your
configuration](https://torsion.org/borgmatic/docs/how-to/upgrade/#upgrading-your-configuration).


### Encryption

Note that if you plan to run borgmatic on a schedule with cron, and you
encrypt your Borg repository with a passphrase instead of a key file, you'll
either need to set the borgmatic `encryption_passphrase` configuration
variable or set the `BORG_PASSPHRASE` environment variable. See the
[repository encryption
section](https://borgbackup.readthedocs.io/en/stable/quickstart.html#repository-encryption)
of the Borg Quick Start for more info.

Alternatively, you can specify the passphrase programatically by setting
either the borgmatic `encryption_passcommand` configuration variable or the
`BORG_PASSCOMMAND` environment variable. See the [Borg Security
FAQ](http://borgbackup.readthedocs.io/en/stable/faq.html#how-can-i-specify-the-encryption-passphrase-programmatically)
for more info.


### Validation

If you'd like to validate that your borgmatic configuration is valid, the
following command is available for that:

```bash
sudo validate-borgmatic-config
```

This command's exit status (`$?` in Bash) is zero when configuration is valid
and non-zero otherwise.

Validating configuration can be useful if you generate your configuration
files via configuration management, or you want to double check that your hand
edits are valid.


## Initialization

Before you can create backups with borgmatic, you first need to initialize a
Borg repository so you have a destination for your backup archives. (But skip
this step if you already have a Borg repository.) To create a repository, run
a command like the following:

```bash
borgmatic init --encryption repokey
```

(No borgmatic `init` action? Try the old-style `--init` flag, or upgrade
borgmatic!)

This uses the borgmatic configuration file you created above to determine
which local or remote repository to create, and encrypts it with the
encryption passphrase specified there if one is provided. Read about [Borg
encryption
modes](https://borgbackup.readthedocs.io/en/stable/usage/init.html#encryption-modes)
for the menu of available encryption modes.

Also, optionally check out the [Borg Quick
Start](https://borgbackup.readthedocs.org/en/stable/quickstart.html) for more
background about repository initialization.

Note that borgmatic skips repository initialization if the repository already
exists. This supports use cases like ensuring a repository exists prior to
performing a backup.

If the repository is on a remote host, make sure that your local user has
key-based SSH access to the desired user account on the remote host.


## Backups

Now that you've configured borgmatic and initialized a repository, it's a
good idea to test that borgmatic is working. So to run borgmatic and start a
backup, you can invoke it like this:

```bash
borgmatic --verbosity 1
```

By default, this will also prune any old backups as per the configured
retention policy, and check backups for consistency problems due to things
like file damage.

The verbosity flag makes borgmatic list the files that it's archiving, which
are those that are new or changed since the last backup. Eyeball the list and
see if it matches your expectations based on the configuration.


## Autopilot

Running backups manually is good for validating your configuration, but I'm
guessing that you want to run borgmatic automatically, say once a day. To do
that, you can configure a separate job runner to invoke it periodically.

### cron

If you're using cron, download the [sample cron
file](https://projects.torsion.org/witten/borgmatic/src/master/sample/cron/borgmatic).
Then, from the directory where you downloaded it:

```bash
sudo mv borgmatic /etc/cron.d/borgmatic
sudo chmod +x /etc/cron.d/borgmatic
```

You can modify the cron file if you'd like to run borgmatic more or less frequently.

### systemd

If you're using systemd instead of cron to run jobs, download the [sample
systemd service
file](https://projects.torsion.org/witten/borgmatic/raw/branch/master/sample/systemd/borgmatic.service)
and the [sample systemd timer
file](https://projects.torsion.org/witten/borgmatic/raw/branch/master/sample/systemd/borgmatic.timer).
Then, from the directory where you downloaded them:

```bash
sudo mv borgmatic.service borgmatic.timer /etc/systemd/system/
sudo systemctl enable borgmatic.timer
sudo systemctl start borgmatic.timer
```

Feel free to modify the timer file based on how frequently you'd like
borgmatic to run.

## Colored output

Borgmatic produces colored terminal output by default. It is disabled when a
non-interactive terminal is detected (like a cron job). Otherwise, you can
disable it by passing the `--no-color` flag, setting the environment variable
`PY_COLORS=False`, or setting the `color` option to `false` in the `output`
section of configuration.

## Troubleshooting

### "found character that cannot start any token" error

If you run borgmatic and see an error looking something like this, it probably
means you've used tabs instead of spaces:

```
test.yaml: Error parsing configuration file
An error occurred while parsing a configuration file at config.yaml:
while scanning for the next token
found character that cannot start any token
  in "config.yaml", line 230, column 1
```

YAML does not allow tabs. So to fix this, replace any tabs in your
configuration file with the requisite number of spaces.

### libyaml compilation errors

borgmatic depends on a Python YAML library (ruamel.yaml) that will optionally
use a C YAML library (libyaml) if present. But if it's not installed, then
when installing or upgrading borgmatic, you may see errors about compiling the
YAML library. If so, not to worry. borgmatic should install and function
correctly even without the C YAML library. And borgmatic won't be any faster
with the C library present, so you don't need to go out of your way to install
it.


## Related documentation

 * [Make per-application backups](https://torsion.org/borgmatic/docs/how-to/make-per-application-backups/)
 * [Deal with very large backups](https://torsion.org/borgmatic/docs/how-to/deal-with-very-large-backups/)
 * [Inspect your backups](https://torsion.org/borgmatic/docs/how-to/inspect-your-backups/)
 * [Monitor your backups](https://torsion.org/borgmatic/docs/how-to/monitor-your-backups/)
 * [Upgrade borgmatic](https://torsion.org/borgmatic/docs/how-to/upgrade/)
 * [borgmatic configuration reference](https://torsion.org/borgmatic/docs/reference/configuration/)
 * [borgmatic command-line reference](https://torsion.org/borgmatic/docs/reference/command-line/)
