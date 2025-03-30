---
title: How to set up backups
eleventyNavigation:
  key: 📥 Set up backups
  parent: How-to guides
  order: 0
---
## Installation

### Prerequisites

First, [install
Borg](https://borgbackup.readthedocs.io/en/stable/installation.html), at least
version 1.1. borgmatic does not install Borg automatically so as to avoid
conflicts with existing Borg installations.

Then, [install pipx](https://pypa.github.io/pipx/installation/) as the root
user (with `sudo`) to make installing borgmatic easier without impacting other
Python applications on your system. If you have trouble installing pipx with
pip, then you can install a system package instead. E.g. on Ubuntu or Debian,
run:

```bash
sudo apt update
sudo apt install pipx
```

### Root install

If you want to run borgmatic on a schedule with privileged access to your
files, then you should install borgmatic as the root user by running the
following commands:

```bash
sudo pipx ensurepath
sudo pipx install borgmatic
```

Check whether this worked with:

```bash
sudo su -
borgmatic --version
```

If borgmatic is properly installed, that should output your borgmatic version.
And if you'd also like `sudo borgmatic` to work, keep reading!


### Non-root install

If you only want to run borgmatic as a non-root user (without privileged file
access) *or* you want to make `sudo borgmatic` work so borgmatic runs as root,
then install borgmatic as a non-root user by running the following commands as
that user:

```bash
pipx ensurepath
pipx install borgmatic
```

This should work even if you've also installed borgmatic as the root user.

Check whether this worked with:

```bash
borgmatic --version
```

If borgmatic is properly installed, that should output your borgmatic version.
You can also try `sudo borgmatic --version` if you intend to run borgmatic
with `sudo`. If that doesn't work, you may need to update your [sudoers
`secure_path` option](https://wiki.archlinux.org/title/Sudo).


### Other ways to install

Besides the approaches described above, there are several other options for
installing borgmatic:

 * [container image with scheduled backups](https://hub.docker.com/r/b3vis/borgmatic/) (+ Docker Compose files)
 * [container image with multi-arch and Docker CLI support](https://hub.docker.com/r/modem7/borgmatic-docker/)
 * [Debian](https://tracker.debian.org/pkg/borgmatic)
 * [Ubuntu](https://launchpad.net/ubuntu/+source/borgmatic)
 * [Fedora official](https://bodhi.fedoraproject.org/updates/?search=borgmatic)
 * [Fedora unofficial](https://copr.fedorainfracloud.org/coprs/heffer/borgmatic/)
 * [Gentoo](https://packages.gentoo.org/packages/app-backup/borgmatic)
 * [Arch Linux](https://archlinux.org/packages/extra/any/borgmatic/)
 * [Alpine Linux](https://pkgs.alpinelinux.org/packages?name=borgmatic)
 * [OpenBSD](https://openports.pl/path/sysutils/borgmatic)
 * [openSUSE](https://software.opensuse.org/package/borgmatic)
 * [macOS (via Homebrew)](https://formulae.brew.sh/formula/borgmatic)
 * [macOS (via MacPorts)](https://ports.macports.org/port/borgmatic/)
 * [NixOS](https://search.nixos.org/packages?show=borgmatic&sort=relevance&type=packages&query=borgmatic)
 * [Ansible role](https://github.com/borgbase/ansible-role-borgbackup)
 * [Unraid](https://unraid.net/community/apps?q=borgmatic#r)


## Hosting providers

Need somewhere to store your encrypted off-site backups? The following hosting
providers include specific support for Borg/borgmatic—and fund borgmatic
development and hosting when you use these referral links to sign up:

<ul>
 <li class="referral"><a href="https://www.borgbase.com/?utm_source=borgmatic">BorgBase</a>: Borg hosting service with support for monitoring, 2FA, and append-only repos</li>
 <li class="referral"><a href="https://hetzner.cloud/?ref=v9dOJ98Ic9I8">Hetzner</a>: A "storage box" that includes support for Borg</li>
</ul>

Additionally, rsync.net has a compatible storage offering, but does not fund
borgmatic development or hosting.


## Configuration

After you install borgmatic, generate a sample configuration file:

```bash
sudo borgmatic config generate
```

<span class="minilink minilink-addedin">Prior to version 1.7.15</span>
Generate a configuration file with this command instead:

```bash
sudo generate-borgmatic-config
```

If neither command is found, then borgmatic may be installed in a location
that's not in your system `PATH` (see above). Try looking in `~/.local/bin/`.

The command generates a sample configuration file at
`/etc/borgmatic/config.yaml` by default. If you'd like to use another path,
use the `--destination` flag, for instance: `--destination
~/.config/borgmatic/config.yaml`.

You should edit the configuration file to suit your needs, as the generated
values are only representative. All options are optional except where
indicated, so feel free to ignore anything you don't need. Be sure to use
spaces rather than tabs for indentation; YAML does not allow tabs.

<span class="minilink minilink-addedin">Prior to version 1.8.0</span> The
configuration file was organized into distinct sections, each with a section
name like `location:` or `storage:`. So in older versions of borgmatic, take
care that if you uncomment a particular option, also uncomment its containing
section name—or else borgmatic won't recognize the option.

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

Alternatively, you can specify the passphrase programmatically by setting
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
sudo borgmatic config validate
```

<span class="minilink minilink-addedin">Prior to version 1.7.15</span>
Validate a configuration file with this command instead:

```bash
sudo validate-borgmatic-config
```

You'll need to specify your configuration file with `--config` if it's not in
a default location.

This command's exit status (`$?` in Bash) is zero when configuration is valid
and non-zero otherwise.

Validating configuration can be useful if you generate your configuration
files via configuration management, or you want to double check that your hand
edits are valid.


## Repository creation

Before you can create backups with borgmatic, you first need to create a Borg
repository so you have a destination for your backup archives. (But skip this
step if you already have a Borg repository.) To create a repository, run a
command like the following with Borg 1.x:

```bash
sudo borgmatic init --encryption repokey
```

<span class="minilink minilink-addedin">New in borgmatic version 1.9.0</span>
Or, with Borg 2.x:

```bash
sudo borgmatic repo-create --encryption repokey-aes-ocb
```

(Note that `repokey-chacha20-poly1305` may be faster than `repokey-aes-ocb` on
certain platforms like ARM64.)

This uses the borgmatic configuration file you created above to determine
which local or remote repository to create and encrypts it with the
encryption passphrase specified there if one is provided. Read about [Borg
encryption
modes](https://borgbackup.readthedocs.io/en/stable/usage/init.html#encryption-mode-tldr)
for the menu of available encryption modes.

Also, optionally check out the [Borg Quick
Start](https://borgbackup.readthedocs.org/en/stable/quickstart.html) for more
background about repository creation.

Note that borgmatic skips repository creation if the repository already
exists. This supports use cases like ensuring a repository exists prior to
performing a backup.

If the repository is on a remote host, make sure that your local user has
key-based SSH access to the desired user account on the remote host.


## Backups

Now that you've configured borgmatic and created a repository, it's a good
idea to test that borgmatic is working. So to run borgmatic and start a
backup, you can invoke it like this:

```bash
sudo borgmatic create --verbosity 1 --list --stats
```

(No borgmatic `--list` flag? Try `--files` instead, leave it out, or upgrade
borgmatic!)

The `--verbosity` flag makes borgmatic show the steps it's performing. The
`--list` flag lists each file that's new or changed since the last backup. And
`--stats` shows summary information about the created archive. All of these
flags are optional.

As the command runs, you should eyeball the output to see if it matches your
expectations based on your configuration.

If you'd like to specify an alternate configuration file path, use the
`--config` flag.

See `borgmatic --help` and `borgmatic create --help` for more information.


## Default actions

If you omit `create` and other actions, borgmatic runs through a set of
default actions: `prune` any old backups as per the configured retention
policy, `compact` segments to free up space (with Borg 1.2+, borgmatic
1.5.23+), `create` a backup, *and* `check` backups for consistency problems
due to things like file damage. For instance:

```bash
sudo borgmatic --verbosity 1 --list --stats
```

### Skipping actions

<span class="minilink minilink-addedin">New in version 1.8.5</span> You can
configure borgmatic to skip running certain actions (default or otherwise).
For instance, to always skip the `compact` action when using [Borg's
append-only
mode](https://borgbackup.readthedocs.io/en/stable/usage/notes.html#append-only-mode-forbid-compaction),
set the `skip_actions` option:

```
skip_actions:
    - compact
```

### Disabling default actions

By default, running `borgmatic` without any arguments will perform the default
backup actions (create, prune, compact and check). If you want to disable this
behavior and require explicit actions to be specified, add the following to
your configuration:

```yaml
default_actions: false
```

With this setting, running `borgmatic` without arguments will show the help
message instead of performing any actions.


## Autopilot

Running backups manually is good for validating your configuration, but I'm
guessing that you want to run borgmatic automatically, say once a day. To do
that, you can configure a separate job runner to invoke it periodically.

### cron

If you're using cron, download the [sample cron
file](https://projects.torsion.org/borgmatic-collective/borgmatic/src/main/sample/cron/borgmatic).
Then, from the directory where you downloaded it:

```bash
sudo mv borgmatic /etc/cron.d/borgmatic
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
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/main/sample/systemd/borgmatic.service)
and the [sample systemd timer
file](https://projects.torsion.org/borgmatic-collective/borgmatic/raw/branch/main/sample/systemd/borgmatic.timer).

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


## Niceties


### Shell completion

borgmatic includes a shell completion script (currently only for Bash and Fish) to
support tab-completing borgmatic command-line actions and flags. Depending on
how you installed borgmatic, this may be enabled by default.

#### Bash

If completions aren't enabled, start by installing the `bash-completion` Linux package or the
[`bash-completion@2`](https://formulae.brew.sh/formula/bash-completion@2)
macOS Homebrew formula. Then, install the shell completion script globally:

```bash
sudo su -c "borgmatic --bash-completion > $(pkg-config --variable=completionsdir bash-completion)/borgmatic"
```

If you don't have `pkg-config` installed, you can try the following path
instead:

```bash
sudo su -c "borgmatic --bash-completion > /usr/share/bash-completion/completions/borgmatic"
```

Or, if you'd like to install the script for only the current user:

```bash
mkdir --parents ~/.local/share/bash-completion/completions
borgmatic --bash-completion > ~/.local/share/bash-completion/completions/borgmatic
```

Finally, restart your shell (`exit` and open a new shell) so the completions
take effect.

#### fish

To add completions for fish, install the completions file globally:

```fish
borgmatic --fish-completion | sudo tee /usr/share/fish/vendor_completions.d/borgmatic.fish
source /usr/share/fish/vendor_completions.d/borgmatic.fish
```

### Colored output

borgmatic produces colored terminal output by default. It is disabled when a
non-interactive terminal is detected (like a cron job), or when you use the
`--json` flag. Otherwise, you can disable it by passing the `--no-color` flag,
setting the environment variables `PY_COLORS=False` or `NO_COLOR=True`, or
setting the `color` option to `false` in the `output` section of
configuration.


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
