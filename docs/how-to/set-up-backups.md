---
title: How to set up backups with borgmatic
---
## Installation

To get up and running, first [install
Borg](https://borgbackup.readthedocs.io/en/latest/installation.html), at
least version 1.1.

Then, run the following command to download and install borgmatic:

```bash
sudo pip3 install --upgrade borgmatic
```

Note that your pip binary may have a different name than "pip3". Make sure
you're using Python 3, as borgmatic does not support Python 2.


### Other ways to install

Along with the above process, you have several other options for installing
borgmatic:

 * [Docker image](https://hub.docker.com/r/monachus/borgmatic/)
 * [Another Docker image](https://hub.docker.com/r/b3vis/borgmatic/)
 * [Debian](https://tracker.debian.org/pkg/borgmatic)
 * [Ubuntu](https://launchpad.net/ubuntu/+source/borgmatic)
 * [Fedora](https://bodhi.fedoraproject.org/updates/?search=borgmatic)
 * [Arch Linux](https://aur.archlinux.org/packages/borgmatic/)
 * [OpenBSD](http://ports.su/sysutils/borgmatic)
 * [openSUSE](https://software.opensuse.org/package/borgmatic)


## Configuration

After you install borgmatic, generate a sample configuration file:

```bash
sudo generate-borgmatic-config
```

If that command is not found, then it may be installed in a location that's
not in your system `PATH`. Try looking in `/usr/local/bin/`.

This generates a sample configuration file at /etc/borgmatic/config.yaml (by
default). You should edit the file to suit your needs, as the values are
representative. All fields are optional except where indicated, so feel free
to ignore anything you don't need.

You can also have a look at the [full configuration
schema](https://projects.torsion.org/witten/borgmatic/src/master/borgmatic/config/schema.yaml)
for the authoritative set of all configuration options. This is handy if
borgmatic has added new options since you originally created your
configuration file.


### Encryption

Note that if you plan to run borgmatic on a schedule with cron, and you
encrypt your Borg repository with a passphrase instead of a key file, you'll
either need to set the borgmatic `encryption_passphrase` configuration
variable or set the `BORG_PASSPHRASE` environment variable. See the
[repository encryption
section](https://borgbackup.readthedocs.io/en/latest/quickstart.html#repository-encryption)
of the Borg Quick Start for more info.

Alternatively, you can specify the passphrase programatically by setting
either the borgmatic `encryption_passcommand` configuration variable or the
`BORG_PASSCOMMAND` environment variable. See the [Borg Security
FAQ](http://borgbackup.readthedocs.io/en/stable/faq.html#how-can-i-specify-the-encryption-passphrase-programmatically)
for more info.


## Initialization

Before you can create backups with borgmatic, you first need to initialize a
Borg repository so you have a destination for your backup archives. (But skip
this step if you already have a Borg repository.) To create a repository, run
a command like the following:

```bash
borgmatic --init --encryption repokey
```

This uses the borgmatic configuration file you created above to determine
which local or remote repository to create, and encrypts it with the
encryption passphrase specified there if one is provided. Read about [Borg
encryption
modes](https://borgbackup.readthedocs.io/en/latest/usage/init.html#encryption-modes)
for the menu of available encryption modes.

Also, optionally check out the [Borg Quick
Start](https://borgbackup.readthedocs.org/en/latest/quickstart.html) for more
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
file](https://projects.torsion.org/witten/borgmatic/src/master/sample/systemd/borgmatic.service)
and the [sample systemd timer
file](https://projects.torsion.org/witten/borgmatic/src/master/sample/systemd/borgmatic.timer).
Then, from the directory where you downloaded them:

```bash
sudo mv borgmatic.service borgmatic.timer /etc/systemd/system/
sudo systemctl enable borgmatic.timer
sudo systemctl start borgmatic.timer
```

Feel free to modify the timer file based on how frequently you'd like
borgmatic to run.


## Related documentation

 * [How to make per-application backups](../../docs/how-to/make-per-application-backups.md)
 * [How to deal with very large backups](../../docs/how-to/deal-with-very-large-backups.md)
 * [How to inspect your backups](../../docs/how-to/inspect-your-backups.md)
 * [borgmatic README](../../../../)
