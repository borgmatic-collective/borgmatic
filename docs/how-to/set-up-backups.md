---
title: How to set up backups
eleventyNavigation:
  key: 📥 Set up backups
  parent: How-to guides
  order: 0
---
## Installation

Many users need to backup system files that require privileged access, so
these instructions install and run borgmatic as root. If you don't need to
backup such files, then you are welcome to install and run borgmatic as a
non-root user.

First, manually [install
Borg](https://borgbackup.readthedocs.io/en/stable/installation.html), at least
version 1.1. borgmatic does not install Borg automatically so as to avoid
conflicts with existing Borg installations.

Then, download and install borgmatic as a [user site
installation](https://packaging.python.org/tutorials/installing-packages/#installing-to-the-user-site)
by running the following command:

```bash
sudo pip3 install --user --upgrade borgmatic
```

This installs borgmatic and its commands at the `/root/.local/bin` path.

Your pip binary may have a different name than "pip3". Make sure you're using
Python 3.7+, as borgmatic does not support older versions of Python.

The next step is to ensure that borgmatic's commands available are on your
system `PATH`, so that you can run borgmatic:

```bash
echo export 'PATH="$PATH:/root/.local/bin"' >> ~/.bashrc
source ~/.bashrc
```

This adds `/root/.local/bin` to your non-root user's system `PATH`.

If you're using a command shell other than Bash, you may need to use different
commands here.

You can check whether all of this worked with:

```bash
sudo borgmatic --version
```

If borgmatic is properly installed, that should output your borgmatic version.

As an alternative to adding the path to `~/.bashrc` file, if you're using sudo
to run borgmatic, you can configure [sudo's
`secure_path` option](https://man.archlinux.org/man/sudoers.5) to include
borgmatic's path.


### Global install option

If you try the user site installation above, and have problems making
borgmatic commands runnable on your system `PATH`, an alternate approach is to
install borgmatic globally.

The following uninstalls borgmatic, and then reinstalls it such that borgmatic
commands are on the default system `PATH`:

```bash
sudo pip3 uninstall borgmatic
sudo pip3 install --upgrade borgmatic
```

The main downside of a global install is that borgmatic is less cleanly
separated from the rest of your Python software, and there's the theoretical
possibility of library conflicts. But if you're okay with that, for instance
on a relatively dedicated system, then a global install can work out fine.


### Other ways to install

Besides the approaches described above, there are several other options for
installing borgmatic:

 * [Docker image with scheduled backups](https://hub.docker.com/r/b3vis/borgmatic/) (+ Docker Compose files)
 * [Docker image with multi-arch and Docker CLI support](https://hub.docker.com/r/modem7/borgmatic-docker/)
 * [Debian](https://tracker.debian.org/pkg/borgmatic)
 * [Ubuntu](https://launchpad.net/ubuntu/+source/borgmatic)
 * [Fedora official](https://bodhi.fedoraproject.org/updates/?search=borgmatic)
 * [Fedora unofficial](https://copr.fedorainfracloud.org/coprs/heffer/borgmatic/)
 * [Arch Linux](https://www.archlinux.org/packages/community/any/borgmatic/)
 * [Alpine Linux](https://pkgs.alpinelinux.org/packages?name=borgmatic)
 * [OpenBSD](http://ports.su/sysutils/borgmatic)
 * [openSUSE](https://software.opensuse.org/package/borgmatic)
 * [Ansible role](https://github.com/borgbase/ansible-role-borgbackup)
 * [virtualenv](https://virtualenv.pypa.io/en/stable/)


## Hosting providers

Need somewhere to store your encrypted off-site backups? The following hosting
providers include specific support for Borg/borgmatic—and fund borgmatic
development and hosting when you use these links to sign up. (These are
referral links, but without any tracking scripts or cookies.)

<ul>
 <li class="referral"><a href="https://www.borgbase.com/?utm_source=borgmatic">BorgBase</a>: Borg hosting service with support for monitoring, 2FA, and append-only repos</li>
</ul>

Additionally, [rsync.net](https://www.rsync.net/products/borg.html) and
[Hetzner](https://www.hetzner.com/storage/storage-box) have compatible storage
offerings, but do not currently fund borgmatic development or hosting.

## Configuration

After you install borgmatic, generate a sample configuration file:

```bash
sudo generate-borgmatic-config
```

If that command is not found, then it may be installed in a location that's
not in your system `PATH` (see above). Try looking in `~/.local/bin/`.

This generates a sample configuration file at `/etc/borgmatic/config.yaml` by
default. If you'd like to use another path, use the `--destination` flag, for
instance: `--destination ~/.config/borgmatic/config.yaml`.

You should edit the configuration file to suit your needs, as the generated
values are only representative. All options are optional except where
indicated, so feel free to ignore anything you don't need.

Note that the configuration file is organized into distinct sections, each
with a section name like `location:` or `storage:`. So take care that if you
uncomment a particular option, also uncomment its containing section name, or
else borgmatic won't recognize the option. Also be sure to use spaces rather
than tabs for indentation; YAML does not allow tabs.

You can get the same sample configuration file from the [configuration
reference](https://torsion.org/borgmatic/docs/reference/configuration/), the
authoritative set of all configuration options. This is handy if borgmatic has
added new options since you originally created your configuration file. Also
check out how to [upgrade your
configuration](https://torsion.org/borgmatic/docs/how-to/upgrade/#upgrading-your-configuration).


### Encryption

If you encrypt your Borg repository with a passphrase or a key file, you'll
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


### Redundancy

If you'd like to configure your backups to go to multiple different
repositories, see the documentation on how to [make backups
redundant](https://torsion.org/borgmatic/docs/how-to/make-backups-redundant/).


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
sudo borgmatic init --encryption repokey
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
sudo borgmatic --verbosity 1 --files
```

(No borgmatic `--files` flag? It's only present in newer versions of
borgmatic. So try leaving it out, or upgrade borgmatic!)

By default, this will also prune any old backups as per the configured
retention policy, compact segments to free up space (with Borg 1.2+), and
check backups for consistency problems due to things like file damage.

The verbosity flag makes borgmatic show the steps it's performing. And the
files flag lists each file that's new or changed since the last backup.
Eyeball the list and see if it matches your expectations based on the
configuration.

If you'd like to specify an alternate configuration file path, use the
`--config` flag. See `borgmatic --help` for more information.


## Autopilot

Running backups manually is good for validating your configuration, but I'm
guessing that you want to run borgmatic automatically, say once a day. To do
that, you can configure a separate job runner to invoke it periodically.

### cron

If you're using cron, download the [sample cron
file](https://projects.torsion.org/borgmatic-collective/borgmatic/src/master/sample/cron/borgmatic).
Then, from the directory where you downloaded it:

```bash
sudo mv borgmatic /etc/cron.d/borgmatic
sudo chmod +x /etc/cron.d/borgmatic
```

If borgmatic is installed at a different location than
`/root/.local/bin/borgmatic`, edit the cron file with the correct path. You
can also modify the cron file if you'd like to run borgmatic more or less
frequently.

### systemd

If you're using systemd instead of cron to run jobs, you can still configure
borgmatic to run automatically.

(If you installed borgmatic from [Other ways to
install](https://torsion.org/borgmatic/docs/how-to/set-up-backups/#other-ways-to-install),
you may already have borgmatic systemd service and timer files. If so, you may
be able to skip some of the steps below.)

First, download the [sample systemd service
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/master/sample/systemd/borgmatic.service)
and the [sample systemd timer
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/master/sample/systemd/borgmatic.timer).

Then, from the directory where you downloaded them:

```bash
sudo mv borgmatic.service borgmatic.timer /etc/systemd/system/
sudo systemctl enable --now borgmatic.timer
```

Review the security settings in the service file and update them as needed.
If `ProtectSystem=strict` is enabled and local repositories are used, then
the repository path must be added to the `ReadWritePaths` list.

Feel free to modify the timer file based on how frequently you'd like
borgmatic to run.

### launchd in macOS

If you run borgmatic in macOS with launchd, you may encounter permissions
issues when reading files to backup. If that happens to you, you may be
interested in an [unofficial work-around for Full Disk
Access](https://projects.torsion.org/borgmatic-collective/borgmatic/issues/293).


## Colored output

Borgmatic produces colored terminal output by default. It is disabled when a
non-interactive terminal is detected (like a cron job), or when you use the
`--json` flag. Otherwise, you can disable it by passing the `--no-color` flag,
setting the environment variable `PY_COLORS=False`, or setting the `color`
option to `false` in the `output` section of configuration.


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
